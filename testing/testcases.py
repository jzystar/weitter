from django.test import TestCase as DjangoTestCase
from django.contrib.auth.models import User
from weits.models import Weit

class TestCase(DjangoTestCase):

    def create_user(self, username, email=None, password=None):
        if password is None:
            password = 'generic password'
        if email is None:
            email = f'{username}@weitter.com'
        return User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )

    def create_weit(self, user, content=None):
        if content is None:
            content = 'default weit content'
        return Weit.objects.create(user=user, content=content)