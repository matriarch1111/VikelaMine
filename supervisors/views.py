from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from core.models import Hazard, HazardResponse, ChecklistItem
from .forms import HazardResponseForm

OVERDUE_HOURS = 24
HIGH_RISK_TYPES = ("OPEN_HOLE", "GAS", "UNSTABLE_GROUND")


def supervisor_required(view_func):
    """Allow only users with role='supervisor'."""
    @login_required
    def wrapper(request, *args, **kwargs):
        if getattr(request.user, "role", None) != "supervisor":
            return redirect("admin:index")
        return view_func(request, *args, **kwargs)
    return wrapper


def _supervisor_sites(user):
    """Return the mining sites this supervisor is responsible for."""
    return user.mining_sites.all()


def _display_status(hazard, now):
    """
    Map a hazard onto one of four dashboard colours.
    There's no severity or 'overdue' field on the model, so this is a
    business rule applied at display time rather than a stored value.
    """
    if hazard.status == "RESOLVED":
        return "resolved"
    age = now - hazard.reported_at
    if age > timedelta(hours=OVERDUE_HOURS):
        return "overdue"
    if hazard.status == "REPORTED" and hazard.hazard_type in HIGH_RISK_TYPES:
        return "critical"
    return "review"


@supervisor_required
def dashboard(request):
    sites = _supervisor_sites(request.user)
    hazards = Hazard.objects.filter(mining_site__in=sites)
    now = timezone.now()
    today = now.date()

    recent_hazards = list(hazards.order_by("-reported_at")[:15])
    for h in recent_hazards:
        h.display_status = _display_status(h, now)

    # Risk by site: unresolved hazard count per site the supervisor covers
    site_rows = []
    open_counts = [
        site.hazards.exclude(status="RESOLVED").count() for site in sites
    ]
    max_open = max(open_counts) if open_counts else 0
    for site, open_count in zip(sites, open_counts):
        pct = round((open_count / max_open) * 100) if max_open else 0
        site_rows.append({"site": site, "open_count": open_count, "pct": pct})

    # Alerts log: derived from hazard and response timestamps (no Alert
    # model exists yet), most recent first.
    alert_events = []
    for h in hazards.order_by("-reported_at")[:20]:
        alert_events.append({
            "kind": "new" if h.status != "RESOLVED" else "resolved",
            "hazard": h,
            "ts": h.reported_at,
        })
    alert_events.sort(key=lambda e: e["ts"], reverse=True)
    alert_events = alert_events[:10]

    # Reports: hazard counts by type, for the bar list
    type_counts = []
    for code, label in Hazard.HAZARD_TYPES:
        count = hazards.filter(hazard_type=code).count()
        if count:
            type_counts.append({"label": label, "count": count})
    max_type = max((t["count"] for t in type_counts), default=0)
    for t in type_counts:
        t["pct"] = round((t["count"] / max_type) * 100) if max_type else 0

    context = {
        "unresolved_count": hazards.exclude(status="RESOLVED").count(),
        "high_risk_count": hazards.filter(
            hazard_type__in=HIGH_RISK_TYPES
        ).exclude(status="RESOLVED").count(),
        "resolved_today_count": hazards.filter(
            status="RESOLVED",
            reported_at__date=today,
        ).count(),
        "pending_tasks_count": ChecklistItem.objects.filter(
            hazard__in=hazards, done=False
        ).count(),
        "recent_hazards": recent_hazards,
        "site_rows": site_rows,
        "alert_events": alert_events,
        "type_counts": type_counts,
    }
    return render(request, "supervisors/dashboard.html", context)


@supervisor_required
def profile(request):
    return render(request, "supervisors/profile.html", {
        "sites": request.user.mining_sites.all(),
    })


@supervisor_required
def hazard_list(request):
    sites = _supervisor_sites(request.user)
    status_filter = request.GET.get("status", "")
    hazards = Hazard.objects.filter(mining_site__in=sites)

    if status_filter:
        hazards = hazards.filter(status=status_filter)

    return render(request, "supervisors/hazard_list.html", {
        "hazards": hazards,
        "status_filter": status_filter,
    })


@supervisor_required
def hazard_detail(request, hazard_id):
    sites = _supervisor_sites(request.user)
    hazard = get_object_or_404(Hazard, id=hazard_id, mining_site__in=sites)
    return render(request, "supervisors/hazard_detail.html", {
        "hazard": hazard,
        "checklist": hazard.checklist_items.all(),
        "responses": hazard.responses.all(),
    })


@supervisor_required
def resolve_hazard(request, hazard_id):
    sites = _supervisor_sites(request.user)
    hazard = get_object_or_404(Hazard, id=hazard_id, mining_site__in=sites)

    if request.method == "POST":
        form = HazardResponseForm(request.POST, request.FILES)
        if form.is_valid():
            for item in hazard.checklist_items.all():
                item.done = request.POST.get(f"item_{item.id}") == "on"
                item.save()

            response = form.save(commit=False)
            response.hazard = hazard
            response.supervisor = request.user
            response.save()

            hazard.status = "RESOLVED"
            hazard.save()

            return redirect("supervisors:hazard_detail", hazard_id=hazard.id)
    else:
        form = HazardResponseForm()

    return render(request, "supervisors/resolve_form.html", {
        "hazard": hazard,
        "form": form,
        "checklist": hazard.checklist_items.all(),
    })


@supervisor_required
def set_status(request, hazard_id, new_status):
    sites = _supervisor_sites(request.user)
    hazard = get_object_or_404(Hazard, id=hazard_id, mining_site__in=sites)

    if new_status in ("INVESTIGATING", "IN_PROGRESS", "RESOLVED"):
        hazard.status = new_status
        hazard.save()

    return redirect("supervisors:hazard_detail", hazard_id=hazard.id)