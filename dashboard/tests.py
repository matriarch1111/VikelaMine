from django.test import TestCase


class DashboardPageTests(TestCase):
	def test_root_route_serves_alerts_page(self):
		response = self.client.get("/")

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "VikelaMine — Alerts")

	def test_navigation_pages_are_served(self):
		page_names = (
			"alerts.html",
			"ai.html",
			"risk-zones.html",
			"users.html",
			"roles.html",
			"reports.html",
			"settings.html",
		)

		for page_name in page_names:
			with self.subTest(page=page_name):
				response = self.client.get(f"/{page_name}")
				self.assertEqual(response.status_code, 200)
				self.assertContains(response, "VikelaMine")

	def test_login_page_is_served(self):
		response = self.client.get("/login/")

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'id="login-email"')
		self.assertContains(response, 'id="login-password"')
		self.assertContains(response, "Log in")

	def test_django_admin_is_not_exposed(self):
		response = self.client.get("/admin/")

		self.assertEqual(response.status_code, 404)

	def test_unknown_page_returns_not_found(self):
		response = self.client.get("/unknown.html")

		self.assertEqual(response.status_code, 404)

	def test_removed_home_page_returns_not_found(self):
		response = self.client.get("/home.html")

		self.assertEqual(response.status_code, 404)
