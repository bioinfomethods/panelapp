from django.urls import reverse_lazy
from django.test import TestCase
from django.test import Client
from faker import Factory
from accounts.models import Reviewer
from .factories import UserFactory
from .factories import ReviewerFactory


fake = Factory.create()


class SetupUsers(TestCase):
    """
    Setup base User and their Reviewer models
    """

    def setUp(self):
        super().setUp()

        self.gel_user = UserFactory(username="gel_user", reviewer__user_type=Reviewer.TYPES.GEL)
        self.verified_user = UserFactory(username="verified_user", reviewer__user_type=Reviewer.TYPES.REVIEWER)
        self.external_user = UserFactory(username="external_user")


class LoginGELUser(SetupUsers):
    """
    LoginGELUser set's up session data on the default Client object available via
    self.client, so in the later tests we don't need to authorise before we make
    the requests.
    """

    def setUp(self):
        super().setUp()
        login_res = self.client.login(username="gel_user", password="pass")
        assert login_res == True
