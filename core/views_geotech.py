# core/views_geotech.py
import math
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from .models import Hazard, MiningSite


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points 
    on Earth (in metres) using the Haversine formula.
    """
    R = 6371000  # Earth's radius in metres
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


@login_required
def check_nearby_hazards(request):
    """
    API endpoint: given a worker's current GPS, return unresolved hazards within a radius.
    Called via AJAX from the worker dashboard.
    """
    try:
        lat = float(request.GET.get('lat'))
        lng = float(request.GET.get('lng'))
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Invalid coordinates'}, status=400)

    radius_m = float(request.GET.get('radius', 100))  # default 100 m

    # Only unresolved hazards (not 'resolved')
    hazards = Hazard.objects.exclude(status='resolved')

    nearby = []
    for h in hazards:
        distance = haversine_distance(lat, lng, h.latitude, h.longitude)
        if distance <= radius_m:
            nearby.append({
                'id': h.id,
                'type': h.get_hazard_type_display(),
                'description': h.description,
                'risk_level': h.risk_level,
                'status': h.status,
                'latitude': h.latitude,
                'longitude': h.longitude,
                'distance_m': round(distance, 1),
                'photo_url': h.photo.url if h.photo else None,
                'created_at': h.created_at.isoformat(),
            })

    nearby.sort(key=lambda x: x['distance_m'])

    return JsonResponse({
        'count': len(nearby),
        'hazards': nearby,
        'radius_m': radius_m,
    })


@login_required
def map_view(request):
    """Render the full map page showing mining sites + hazards."""
    # Supervisors see only their site; admins see all
    if request.user.role == 'supervisor' and request.user.mining_site:
        sites = MiningSite.objects.filter(id=request.user.mining_site.id)
        hazards = Hazard.objects.filter(mining_site=request.user.mining_site)
    else:
        sites = MiningSite.objects.all()
        hazards = Hazard.objects.all()

    return render(request, 'core/map.html', {
        'sites': sites,
        'hazards': hazards,
    })


@login_required
def hazard_map_data(request):
    """JSON feed of all hazards for the map."""
    hazards = Hazard.objects.all()
    if request.user.role == 'supervisor' and request.user.mining_site:
        hazards = hazards.filter(mining_site=request.user.mining_site)

    data = [{
        'id': h.id,
        'type': h.get_hazard_type_display(),
        'description': h.description,
        'latitude': h.latitude,
        'longitude': h.longitude,
        'status': h.status,
        'risk_level': h.risk_level,
        'photo_url': h.photo.url if h.photo else None,
        'mining_site': h.mining_site.name if h.mining_site else '',
        'created_at': h.created_at.strftime('%Y-%m-%d %H:%M'),
    } for h in hazards]

    sites_data = [{
        'id': s.id,
        'name': s.name,
        'latitude': s.latitude,
        'longitude': s.longitude,
        'status': s.status,
    } for s in MiningSite.objects.all()]

    return JsonResponse({'hazards': data, 'sites': sites_data})