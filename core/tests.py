import os
import json
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from .models import Hazard, MiningSite, PanicAlert, User


class HazardSubmissionSyncTests(TestCase):
	def test_retried_submission_id_does_not_create_duplicate_hazard(self):
		payload = {
			'client_submission_id': '78a8c58c-e381-48be-b49d-d64f08a48e5e',
			'hazard_type': 'gas',
			'description': 'Gas detected near the main shaft.',
		}

		first_response = self.client.post(reverse('report_hazard'), payload)
		retry_response = self.client.post(reverse('report_hazard'), payload)

		self.assertEqual(first_response.status_code, 200)
		self.assertTrue(first_response.json()['created'])
		self.assertEqual(retry_response.status_code, 200)
		self.assertFalse(retry_response.json()['created'])
		self.assertEqual(Hazard.objects.count(), 1)


class AIChatTests(TestCase):
	@patch.dict(os.environ, {'OPENAI_API_KEY': ''})
	def test_chat_requires_report_evidence(self):
		response = self.client.post(
			reverse('ai_chat'),
			{'message': 'What should I do?', 'language': 'en-US'},
		)

		self.assertEqual(response.status_code, 400)
		self.assertIn('report details, a voice note, or an image', response.json()['error'])

	@patch.dict(os.environ, {'OPENAI_API_KEY': ''})
	def test_chat_explains_missing_api_key_for_report_evidence(self):
		response = self.client.post(reverse('ai_chat'), {
			'message': 'What should I do?',
			'description': 'Gas is leaking by the ventilation shaft.',
			'language': 'en-US',
		})

		self.assertEqual(response.status_code, 503)
		self.assertIn('OPENAI_API_KEY', response.json()['error'])

	@patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
	@patch('core.views.OpenAI')
	def test_chat_returns_a_model_reply(self, openai_client):
		openai_client.return_value.chat.completions.create.return_value = SimpleNamespace(
			choices=[SimpleNamespace(message=SimpleNamespace(content='Move away and alert your supervisor.'))]
		)
		response = self.client.post(
			reverse('ai_chat'),
			{
				'message': 'What should I do?',
				'description': 'Gas is leaking by the ventilation shaft.',
				'language': 'en-US',
				'history': '[]',
			},
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()['reply'], 'Move away and alert your supervisor.')
		openai_client.return_value.chat.completions.create.assert_called_once()
		messages = openai_client.return_value.chat.completions.create.call_args.kwargs['messages']
		self.assertIn('Gas is leaking by the ventilation shaft.', messages[-1]['content'][0]['text'])

	@patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
	@patch('core.views.OpenAI')
	def test_chat_transcribes_and_uses_only_attached_voice_note(self, openai_client):
		openai_client.return_value.audio.transcriptions.create.return_value = SimpleNamespace(
			text='Gas is leaking beside the west ventilation shaft.'
		)
		openai_client.return_value.chat.completions.create.return_value = SimpleNamespace(
			choices=[SimpleNamespace(message=SimpleNamespace(content='Move away and notify your supervisor.'))]
		)
		voice_note = SimpleUploadedFile('report.webm', b'voice-data', content_type='audio/webm')

		response = self.client.post(reverse('ai_chat'), {
			'message': 'What should I do?',
			'language': 'en-US',
			'history': '[]',
			'voice_note': voice_note,
		})

		self.assertEqual(response.status_code, 200)
		openai_client.return_value.audio.transcriptions.create.assert_called_once()
		messages = openai_client.return_value.chat.completions.create.call_args.kwargs['messages']
		self.assertIn('Gas is leaking beside the west ventilation shaft.', messages[-1]['content'][0]['text'])


class ReportMediaTests(TestCase):
	def test_voice_note_and_language_are_saved_with_report(self):
		with tempfile.TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
			voice_note = SimpleUploadedFile('voice-note.webm', b'voice-data', content_type='audio/webm')
			response = self.client.post(reverse('report_hazard'), {
				'client_submission_id': 'd1d2c258-2a0f-4ced-a3d3-cbda43388477',
				'hazard_type': 'gas',
				'description': 'There is gas near the west tunnel.',
				'description_language': 'zu-ZA',
				'voice_note': voice_note,
			})

		self.assertEqual(response.status_code, 200)
		hazard = Hazard.objects.get()
		self.assertEqual(hazard.description_language, 'zu-ZA')
		self.assertTrue(hazard.voice_note.name.endswith('voice-note.webm'))

	def test_voice_only_report_can_be_saved_before_transcription(self):
		with tempfile.TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
			voice_note = SimpleUploadedFile('voice-only.webm', b'voice-data', content_type='audio/webm')
			response = self.client.post(reverse('report_hazard'), {
				'client_submission_id': '03bfb3c4-1b8d-4a53-9fc1-14048468d0ea',
				'hazard_type': 'gas',
				'description': '',
				'description_language': 'zu-ZA',
				'voice_note': voice_note,
			})

		self.assertEqual(response.status_code, 200)
		hazard = Hazard.objects.get()
		self.assertIn('transcription pending', hazard.description)
		self.assertTrue(hazard.voice_note)


class SOSAlertTests(TestCase):
	def test_sos_alert_is_saved_with_valid_coordinates(self):
		response = self.client.post(
			reverse('sos_alert'),
			data=json.dumps({'latitude': -28.7414, 'longitude': 24.7716}),
			content_type='application/json',
		)

		self.assertEqual(response.status_code, 201)
		alert = PanicAlert.objects.get()
		self.assertAlmostEqual(alert.latitude, -28.7414)
		self.assertAlmostEqual(alert.longitude, 24.7716)

	@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
	def test_sos_notifies_supervisor_with_configured_email(self):
		User.objects.create_user(username='safety-lead', password='test-pass', role=User.SUPERVISOR, email='lead@example.com')
		response = self.client.post(
			reverse('sos_alert'),
			data=json.dumps({'latitude': -28.7, 'longitude': 24.8}),
			content_type='application/json',
		)

		self.assertEqual(response.status_code, 201)
		self.assertTrue(response.json()['notified'])
		self.assertEqual(len(mail.outbox), 1)
		self.assertIn('-28.7, 24.8', mail.outbox[0].body)

	def test_sos_alert_is_still_saved_if_location_is_unavailable(self):
		response = self.client.post(
			reverse('sos_alert'),
			data='{}',
			content_type='application/json',
		)

		self.assertEqual(response.status_code, 201)
		self.assertIsNone(PanicAlert.objects.get().latitude)


class DashboardReportTests(TestCase):
	def test_dashboard_and_reports_show_saved_report_and_alert_data(self):
		Hazard.objects.create(
			hazard_type='gas',
			description='Gas was detected near the west tunnel.',
			description_language='en-US',
		)
		PanicAlert.objects.create(latitude=-28.7, longitude=24.8, note='Emergency SOS')

		dashboard = self.client.get(reverse('dashboard'))
		reports = self.client.get(reverse('reports'))

		self.assertEqual(dashboard.status_code, 200)
		self.assertContains(dashboard, 'Gas was detected near the west tunnel.')
		self.assertContains(dashboard, 'Recent SOS alerts')
		self.assertContains(dashboard, 'Translate')
		self.assertEqual(reports.status_code, 200)
		self.assertContains(reports, 'Gas was detected near the west tunnel.')
		self.assertContains(reports, 'Speak text')


class HazardMapDataTests(TestCase):
	def test_map_api_returns_distinct_numeric_hazard_and_site_coordinates(self):
		first = Hazard.objects.create(
			hazard_type='open_hole',
			description='Near the east access tunnel.',
			latitude=-28.7451,
			longitude=24.7643,
			status='reported',
		)
		second = Hazard.objects.create(
			hazard_type='gas',
			description='Near the west ventilation shaft.',
			latitude=-29.1,
			longitude=25.2,
			status='resolved',
		)
		MiningSite.objects.create(name='North Shaft', latitude=-28.8, longitude=24.9)
		Hazard.objects.create(hazard_type='other', description='No GPS available.')

		response = self.client.get(reverse('hazard_map_data'))

		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertEqual(len(payload['hazards']), 2)
		self.assertEqual(len(payload['sites']), 1)
		first_response = next(item for item in payload['hazards'] if item['id'] == first.id)
		second_response = next(item for item in payload['hazards'] if item['id'] == second.id)
		self.assertEqual((first_response['latitude'], first_response['longitude']), (-28.7451, 24.7643))
		self.assertEqual((second_response['latitude'], second_response['longitude']), (-29.1, 25.2))
		self.assertEqual(first_response['status'], 'reported')
		self.assertEqual(second_response['status'], 'resolved')
		self.assertEqual((payload['sites'][0]['latitude'], payload['sites'][0]['longitude']), (-28.8, 24.9))

	def test_map_page_uses_registered_api_and_has_no_fake_test_pin(self):
		response = self.client.get(reverse('maps'))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, reverse('hazard_map_data'))
		self.assertNotContains(response, 'VikelaMine Test')
		self.assertNotContains(response, "fetch('/api/hazard-map-data/')")


class PageRoutingTests(TestCase):
	def test_old_ai_url_redirects_to_report_page(self):
		response = self.client.get(reverse('ai_assistance'))
		self.assertRedirects(response, reverse('report_hazard'))

	def test_service_worker_can_control_root_pages(self):
		response = self.client.get(reverse('service_worker'))
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response['Service-Worker-Allowed'], '/')
		self.assertContains(response, '/report-hazard/')


class ReportLanguageServiceTests(TestCase):
	@patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
	@patch('core.views.OpenAI')
	def test_translation_returns_target_language_text(self, openai_client):
		openai_client.return_value.chat.completions.create.return_value = SimpleNamespace(
			choices=[SimpleNamespace(message=SimpleNamespace(content='Kukhona igesi emhubheni osentshonalanga.'))]
		)
		response = self.client.post(
			reverse('translate_report_text'),
			data=json.dumps({
				'text': 'There is gas in the west tunnel.',
				'source_language': 'en-US',
				'target_language': 'zu-ZA',
			}),
			content_type='application/json',
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()['translation'], 'Kukhona igesi emhubheni osentshonalanga.')

	@patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
	@patch('core.views.OpenAI')
	def test_interface_batch_translates_strings_in_order(self, openai_client):
		openai_client.return_value.chat.completions.create.return_value = SimpleNamespace(
			choices=[SimpleNamespace(message=SimpleNamespace(content='{"translations":["Ikhaya","Imibiko"]}'))]
		)
		response = self.client.post(
			reverse('translate_interface'),
			data=json.dumps({'texts': ['Home', 'Reports'], 'target_language': 'zu-ZA'}),
			content_type='application/json',
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()['translations'], ['Ikhaya', 'Imibiko'])

	@patch.dict(os.environ, {'OPENAI_API_KEY': ''})
	def test_interface_translation_reports_missing_key(self):
		response = self.client.post(
			reverse('translate_interface'),
			data=json.dumps({'texts': ['Home'], 'target_language': 'zu-ZA'}),
			content_type='application/json',
		)

		self.assertEqual(response.status_code, 503)

	@patch.dict(os.environ, {'OPENAI_API_KEY': ''})
	def test_voice_transcription_reports_missing_ai_configuration(self):
		voice_note = SimpleUploadedFile('note.webm', b'voice-data', content_type='audio/webm')
		response = self.client.post(reverse('transcribe_voice_note'), {'audio': voice_note})

		self.assertEqual(response.status_code, 503)
		self.assertIn('OPENAI_API_KEY', response.json()['error'])
