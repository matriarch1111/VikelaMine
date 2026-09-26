from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class SupervisorAccountTests(TestCase):
	def setUp(self):
		self.user = get_user_model().objects.create_user(
			username="supervisor",
			password="test-password",
			role="supervisor",
		)

	def test_profile_requires_login(self):
		response = self.client.get(reverse("supervisors:profile"))

		self.assertRedirects(
			response,
			"/accounts/login/?next=/supervisor/profile/",
		)

	def test_supervisor_can_view_profile(self):
		self.client.force_login(self.user)

		response = self.client.get(reverse("supervisors:profile"))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Supervisor profile")
		self.assertContains(response, "supervisor")

	def test_logout_ends_session_and_redirects_to_login(self):
		self.client.force_login(self.user)

		response = self.client.post(reverse("logout"))

		self.assertRedirects(response, "/accounts/login/")
		self.assertNotIn("_auth_user_id", self.client.session)
