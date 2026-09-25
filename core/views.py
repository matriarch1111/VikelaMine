from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login



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
        print(request.POST.dict())

        return redirect('/reports/')

    return render(request, 'core/report_hazard.html')


def reports(request):
    return render(request, 'core/my_reports.html')


def add_report(request):
    return render(request, 'core/add_report.html')


# =========================
# MAP / DANGER
# =========================
from django.conf import settings
from django.http import JsonResponse

def maps(request):
    return render(request, 'core/maps.html', {
        'GOOGLE_MAPS_API_KEY': getattr(settings, 'GOOGLE_MAPS_API_KEY', 'YOUR_KEY_HERE')
    })

def hazard_map_data(request):
    hazards = []
    for h in HazardReport.objects.exclude(latitude__isnull=True):
        hazards.append({
            "latitude": float(h.latitude),
            "longitude": float(h.longitude),
            "type": h.hazard_type,
            "description": h.description,
            "status": getattr(h, 'status', 'reported'),
            "risk_level": getattr(h, 'risk_level', 'High'),
            "photo_url": h.photo.url if getattr(h, 'photo', None) else "",
        })
    sites = []
    # if you have MiningSite model
    try:
        for s in MiningSite.objects.exclude(latitude__isnull=True):
            sites.append({"name": s.name, "latitude": float(s.latitude), "longitude": float(s.longitude)})
    except: pass

    return JsonResponse({"hazards": hazards, "sites": sites})
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