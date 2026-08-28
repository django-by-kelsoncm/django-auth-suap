from unittest.mock import MagicMock

from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase
from django.urls import reverse

from .apps import SuapAuthImpersonationConfig
from .context_processors import impersonation as impersonation_cp
from .helpers import get_active_user, is_impersonating
from .views import ImpersonateView

User = get_user_model()


class ImpersonationAppConfigTestCase(TestCase):
    def test_app_config(self):
        app_config = apps.get_app_config("django_suap_auth_impersonation")
        self.assertEqual(app_config.name, "django_suap_auth.impersonation")
        self.assertEqual(app_config.label, "django_suap_auth_impersonation")
        self.assertIsInstance(app_config, SuapAuthImpersonationConfig)


class ImpersonationHelpersTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.superuser = User.objects.create_superuser(username="admin", email="admin@example.com")
        self.normal_user = User.objects.create_user(username="student", email="student@example.com")
        self.other_admin = User.objects.create_superuser(username="other_admin", email="other@example.com")

    def test_get_active_user_edge_cases(self):
        self.assertIsNone(get_active_user(None))

        req = self.factory.get("/")
        req.user = MagicMock(is_authenticated=False)
        self.assertEqual(get_active_user(req), req.user)

        req.user = self.normal_user
        req.session = {}
        self.assertEqual(get_active_user(req), self.normal_user)

        req.user = self.superuser
        req.session = {}
        self.assertEqual(get_active_user(req), self.superuser)

        req.session = {"impersonated_user": "non_existent"}
        self.assertEqual(get_active_user(req), self.superuser)

        req.session = {"impersonated_user": "other_admin"}
        self.assertEqual(get_active_user(req), self.superuser)

        req.session = {"impersonated_user": "student"}
        self.assertEqual(get_active_user(req), self.normal_user)

    def test_is_impersonating_edge_cases(self):
        self.assertFalse(is_impersonating(None))

        req = self.factory.get("/")
        req.user = MagicMock(is_authenticated=False)
        self.assertFalse(is_impersonating(req))

        req.user = self.normal_user
        req.session = {"impersonated_user": "student"}
        self.assertFalse(is_impersonating(req))

        req.user = self.superuser
        req.session = {}
        self.assertFalse(is_impersonating(req))

        req.session = {"impersonated_user": "non_existent"}
        self.assertFalse(is_impersonating(req))

        req.session = {"impersonated_user": "other_admin"}
        self.assertFalse(is_impersonating(req))

        req.session = {"impersonated_user": "student"}
        self.assertTrue(is_impersonating(req))


class ImpersonationContextProcessorTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.superuser = User.objects.create_superuser(username="admin", email="admin@example.com")
        self.normal_user = User.objects.create_user(username="student", email="student@example.com")

    def test_context_processor(self):
        req = self.factory.get("/")
        req.user = self.superuser
        req.session = {"impersonated_user": "student"}

        ctx = impersonation_cp(req)
        self.assertEqual(ctx["active_user"], self.normal_user)
        self.assertTrue(ctx["is_impersonating"])


class ImpersonationViewsTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.superuser = User.objects.create_superuser(username="admin", email="admin@example.com")
        self.normal_user = User.objects.create_user(username="student", email="student@example.com")
        self.other_admin = User.objects.create_superuser(username="other_admin", email="other@example.com")

    def test_impersonate_permission_denied_for_anonymous_or_normal_user(self):
        self.client.logout()
        url = reverse("suap_auth_impersonation:impersonate", kwargs={"username": "student"})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        self.client.force_login(self.normal_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_impersonate_missing_username(self):
        self.client.force_login(self.superuser)
        url = reverse("suap_auth_impersonation:impersonate_param")

        response = self.client.get(url, follow=True)
        self.assertRedirects(response, "/dashboard/")
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("Username is required for impersonation.", messages)

    def test_impersonate_nested_forbidden(self):
        self.client.force_login(self.superuser)
        session = self.client.session
        session["impersonated_user"] = "student"
        session.save()

        url = reverse("suap_auth_impersonation:impersonate", kwargs={"username": "student"})
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, "/dashboard/")
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("Nested impersonation is not allowed.", messages)

    def test_impersonate_non_existent_user(self):
        self.client.force_login(self.superuser)
        url = reverse("suap_auth_impersonation:impersonate", kwargs={"username": "ghost"})

        response = self.client.get(url, follow=True)
        self.assertRedirects(response, "/dashboard/")
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("User 'ghost' does not exist.", messages)

    def test_impersonate_other_superuser_forbidden(self):
        self.client.force_login(self.superuser)
        url = reverse("suap_auth_impersonation:impersonate", kwargs={"username": "other_admin"})

        response = self.client.get(url, follow=True)
        self.assertRedirects(response, "/dashboard/")
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("Impersonating another superuser is not allowed.", messages)

    def test_impersonate_success_and_redirect(self):
        self.client.force_login(self.superuser)
        url = reverse("suap_auth_impersonation:impersonate", kwargs={"username": "student"}) + "?next=/profile/"

        response = self.client.get(url, follow=True)
        self.assertRedirects(response, "/profile/")
        self.assertEqual(self.client.session.get("impersonated_user"), "student")
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("You are now impersonating student.", messages)

    def test_impersonate_post_request(self):
        self.client.force_login(self.superuser)
        url = reverse("suap_auth_impersonation:impersonate_param")

        response = self.client.post(url, {"username": "student"}, follow=True)
        self.assertRedirects(response, "/dashboard/")
        self.assertEqual(self.client.session.get("impersonated_user"), "student")

    def test_stop_impersonating(self):
        self.client.force_login(self.superuser)
        session = self.client.session
        session["impersonated_user"] = "student"
        session.save()

        url = reverse("suap_auth_impersonation:stop_impersonating") + "?next=/home/"
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, "/home/")
        self.assertNotIn("impersonated_user", self.client.session)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("Impersonation ended successfully.", messages)

    def test_stop_impersonating_post(self):
        self.client.force_login(self.superuser)
        url = reverse("suap_auth_impersonation:stop_impersonating")

        response = self.client.post(url, follow=True)
        self.assertRedirects(response, "/dashboard/")

    def test_impersonate_view_permission_denied_exception_handler(self):
        request = self.factory.get("/")
        request.user = self.normal_user
        view = ImpersonateView()
        with self.assertRaises(PermissionDenied):
            view.get(request, username="student")
