# VikelaMine Backend

Django + Django REST Framework + MySQL backend for the VikelaMine mine-worker
safety platform (GeoTech for Impact hackathon). Matches the tech stack from
the team profile form: Django/Python, Django REST Framework, Django
Authentication, MySQL, Cloudinary.

## What's included

| App | Responsibility |
|---|---|
| `accounts` | Custom user model with roles (Worker, Supervisor, Mine Manager, OHS Manager, Rescue Team, Admin), preferred language, per-channel alert prefs (audio/vibration/visual), JWT login |
| `sites_app` | MiningSite + Zone models; zones carry a risk level that maps to a map color |
| `hazards` | HazardReport (photo, GPS, AI analysis, translations), offline-sync endpoint, 30-day worker-view purge, pluggable AI service layer |
| `checklists` | Auto-created supervisor checklist item per hazard; completing it resolves the hazard |
| `alerts` | Proximity-alert engine (5-min cooldown), notifications, offline-safe emergency guidance |
| `core` | Shared role-based permissions, haversine distance util, demo data seeder |

## How the spec maps to the code

- **Hazard reporting (photo + note + GPS)** → `POST /api/hazards/` (multipart: `photo`, `description`, `latitude`, `longitude`, `mining_site`, `category`).
- **Map with risk colors** → `GET /api/zones/` returns each zone's `current_risk_level` and a ready-to-use `color` hex value.
- **History, purged after 30 days (worker side only)** → resolved hazards are never deleted; `hazards.tasks.purge_resolved_hazards` (Celery, hourly) or `python manage.py purge_resolved_hazards` sets `hidden_from_workers=True` once `resolved_at` is 30+ days old. Workers' hazard list excludes hidden ones; supervisors/admins still see everything.
- **Supervisor checklist, remaining tasks only** → `checklists/signals.py` creates a `ChecklistItem` on every new hazard; `GET /api/checklists/` defaults to `is_done=False` (`?include_done=1` for full history).
- **Offline capture, synced later** → mobile app queues reports locally with a client-generated UUID, then `POST /api/hazards/sync/` with a batch; duplicate UUIDs are silently skipped so retries are safe.
- **Connecting roles** → `role` field on `User` plus `supervisor` FK (worker → supervisor); permission classes in `core/permissions.py` gate who can acknowledge/resolve/manage.
- **Multilingual (EN, isiZulu, Setswana, Afrikaans, Xitsonga)** → `HazardReport.translated_text` JSON field, populated via `hazards/ai_services.translate_text`; swap in any translation provider by editing that one file. Emergency guidance can be requested pre-translated: `GET /api/alerts/emergency-guidance/?type=GAS_VENTILATION&language=zu`.
- **Proximity alerts (audio/vibration/visual, every 5 min, accessible to deaf/non-speaking workers)** → `alerts/services.check_and_alert` compares a worker's last-known GPS to open hazards' zone radius, respects the user's chosen channels, and only re-fires after `PROXIMITY_ALERT_REPEAT_SECONDS` (300s). Runs via a Celery beat sweep (`alerts.tasks.sweep_proximity_alerts`) or can be called on-demand: `POST /api/alerts/proximity-check/`.
- **AI image analysis + suggested solution** → `hazards/ai_services.analyze_hazard_image`, called automatically when a hazard photo is uploaded; result stored in `HazardReport.ai_analysis`. Wire in your chosen vision model by filling in the request in that function.
- **Admin: manage accounts, permissions, GPS layout, monitor activity** → `/api/auth/users/` (list/edit/delete), `/api/sites/` + `/api/zones/` (admin-write), Django admin at `/admin/` for full activity visibility.

## Local setup

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in DB + Cloudinary + AI provider credentials

# Create the MySQL database first, e.g.:
#   CREATE DATABASE vikelamine CHARACTER SET utf8mb4;

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo_data     # optional: demo site, zones, one user per role (password: Demo@12345)
python manage.py runserver
```

To run the background jobs (30-day purge + proximity sweep) you'll also need Redis and:
```bash
celery -A vikelamine worker -l info
celery -A vikelamine beat -l info
```
If you don't want to stand up Celery/Redis for the hackathon demo, the purge can be run manually or via a simple cron job instead:
```bash
python manage.py purge_resolved_hazards
```

## Key API endpoints

```
POST   /api/auth/register/
POST   /api/auth/login/                 -> {access, refresh}
POST   /api/auth/login/refresh/
GET    /api/auth/me/                    -> current user profile
PATCH  /api/auth/me/                    -> update language/alert prefs
POST   /api/auth/me/location/           -> {latitude, longitude} location ping
GET    /api/auth/users/                 -> admin: list accounts
GET    /api/auth/users/<id>/            -> admin: view/edit/remove account

GET    /api/sites/                      -> mining sites (+ nested zones)
GET    /api/zones/                      -> map data: zones with risk color
GET    /api/hazards/categories/
GET    /api/hazards/                    -> list (role-scoped)
POST   /api/hazards/                    -> report a hazard (photo, GPS, note)
POST   /api/hazards/<id>/acknowledge/
POST   /api/hazards/<id>/resolve/
GET    /api/hazards/updates/?hazard=<id>
POST   /api/hazards/updates/            -> supervisor follow-up note/photo
POST   /api/hazards/sync/               -> offline batch sync

GET    /api/checklists/                 -> remaining tasks (supervisor dashboard)
POST   /api/checklists/<id>/complete/

GET    /api/alerts/notifications/
POST   /api/alerts/notifications/<id>/read/
POST   /api/alerts/proximity-check/     -> {latitude, longitude} -> fired alerts
GET    /api/alerts/emergency-guidance/?type=GAS_VENTILATION&language=zu
```

## Notes / next steps for the team

- `mysqlclient` needs `libmysqlclient-dev` (or `default-libmysqlclient-dev` on Debian/Ubuntu) installed on whatever machine runs `pip install`.
- Cloudinary is wired as the default file storage for hazard photos/audio; without credentials in `.env` it'll error on upload — for local dev without Cloudinary, switch `DEFAULT_FILE_STORAGE` in `settings.py` to `django.core.files.storage.FileSystemStorage`.
- `hazards/ai_services.py` is intentionally a thin, swappable layer — plug in whatever vision/translation/speech API you settle on (OpenAI, Google Cloud, Azure, etc.) without touching any other app.
- Speech-to-text/text-to-speech endpoints are implemented in `ai_services.py` but not yet wired to a view — add a small `POST /api/hazards/voice-note/` view calling `speech_to_text` when you're ready to accept audio hazard notes.