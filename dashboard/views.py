from django.conf import settings
from django.http import Http404, HttpResponse

PAGE_FILES = {
	"login": "login",
	"alerts": "alerts",
	"ai": "AI",
	"risk-zones": "risk_zones",
	"users": "users",
	"roles": "roles",
	"reports": "reports",
	"settings": "settings",
}


def page(request, page_name):
	source_name = PAGE_FILES.get(page_name)
	if source_name is None:
		raise Http404("Page not found")

	html = (settings.BASE_DIR / source_name).read_text(encoding="utf-8")
	return HttpResponse(html, content_type="text/html; charset=utf-8")
