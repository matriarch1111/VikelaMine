from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login
from .models import Hazard, MiningSite
from django.conf import settings



# =========================
# PUBLIC PAGES
# =========================

def home(request):
    return render(request, 'core/landing.html')


def features(request):
    return render(request, 'core/features.html')


def how_it_works(request):
    return render(request, 'core/how_it_works.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)

            # After successful login, go directly to Report Hazard
            return redirect('report_hazard')

        else:
            return render(request, 'core/login.html', {
                'error': 'Invalid username or password.'
            })

    return render(request, 'core/login.html')

# =========================
# MAIN DASHBOARD
# =========================

def dashboard(request):
    return render(request, 'core/dashboard.html', {
        'hazards': [],
        'open_count': 0,
        'resolved': 0,
        'sos_count': 0,
        'users_count': 0,
    })


# =========================
# RECORD
# =========================

def report_hazard(request):

    if request.method == 'POST':

        hazard = Hazard.objects.create(
            hazard_type=request.POST.get('hazard_type'),
            description=request.POST.get('description'),
            latitude=request.POST.get('latitude') or None,
            longitude=request.POST.get('longitude') or None,
            reported_by=request.user if request.user.is_authenticated else None,
            photo=request.FILES.get('photo')
        )

        return redirect('/reports/')

    return render(request, 'core/report_hazard.html')


def reports(request):
    return render(request, 'core/my_reports.html')


def add_report(request):
    return render(request, 'core/add_report.html')


# =========================
# MAP / DANGER
# =========================


def maps(request):
    return render(request, 'core/maps.html', {
        'GOOGLE_MAPS_API_KEY': getattr(settings, 'GOOGLE_MAPS_API_KEY', 'YOUR_KEY_HERE')
    })

def hazard_map_data(request):

    hazards = []

    for h in Hazard.objects.exclude(
        latitude__isnull=True
    ).exclude(
        longitude__isnull=True
    ):

        hazards.append({
            "id": h.id,
            "latitude": h.latitude,
            "longitude": h.longitude,
            "type": h.get_hazard_type_display(),
            "description": h.description,
            "status": h.status,
            "priority": h.priority,
            "photo_url": h.photo.url if h.photo else "",
        })

    sites = []

    for s in MiningSite.objects.all():

        sites.append({
            "name": s.name,
            "latitude": s.latitude,
            "longitude": s.longitude,
            "status": s.status,
        })

    return JsonResponse({
        "hazards": hazards,
        "sites": sites
    })
def nearby_danger(request):
    return render(request, 'core/nearby_danger.html')

def check_nearby_hazards(request):
    from django.http import JsonResponse
    return JsonResponse({"hazards": []})

# =========================
# HAZARD
# =========================

def hazard_detail(request, id):
    return render(request, 'core/hazard_detail.html', {
        'hazard_id': id
    })


def resolve_hazard(request, id):
    return render(request, 'core/resolve_hazard.html', {
        'hazard_id': id
    })


# =========================
# PREVENT
# =========================

def summaries(request):
    return render(request, 'core/summaries.html')


# =========================
# PANIC / SOS
# =========================

def panic(request):
    return render(request, 'core/panic.html')


def sos_alert(request):
    return JsonResponse({
        "ok": True,
        "message": "SOS received"
    })


# =========================
# OTHER PAGES
# =========================

def documents(request):
    return render(request, 'core/documents.html')


def faq(request):
    return render(request, 'core/faq.html')


def pricing(request):
    return render(request, 'core/pricing.html')


def contact(request):
    return render(request, 'core/faq.html')


def settings_page(request):
    return render(request, 'core/admin_dashboard.html', {
        'users': [],
        'sites': [],
    })

def admin_users(request):
    return render(request, 'core/admin_users.html', {
        'users': [],
    })


def admin_sites(request):
    return render(request, 'core/admin_sites.html', {
        'sites': [],
    })

def forgot_password(request):
    return render(request, 'core/forgot_password.html', {
        'sites': [],
    })

from django.http import JsonResponse

def check_nearby_hazards(request):
    lat = request.GET.get('lat')
    lng = request.GET.get('lng')
    # for now return empty - you can add real logic later
    return JsonResponse({"hazards": []})

def settings_view(request):
    return render(request, 'core/settings.html')