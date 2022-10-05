from django.contrib.auth.models import User
from django.test import TestCase as DjangoTestCase
from rest_framework.test import APIClient
from weits.models import Weit
from comments.models import Comment

class TestCase(DjangoTestCase):

    @property
    def anonymous_client(self):
        if hasattr(self, '_anonymous_client'):
            return self._anonymous_client
        self._anonymous_client = APIClient()
        return self._anonymous_client

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

    def create_comment(self, user, weit, content=None):
        if content is None:
            content = 'default comment content'
        return Comment.objects.create(user=user, weit=weit, content=content)
