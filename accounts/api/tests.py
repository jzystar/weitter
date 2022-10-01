from testing.testcases import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User

LOGIN_URL = '/api/accounts/login/'
LOGOUT_URL = '/api/accounts/logout/'
SIGNUP_URL = '/api/accounts/signup/'
LOGIN_STATUS_URL = '/api/accounts/login_status/'


class AccountAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.correct_password = 'password_test'
        self.user = self.create_user(
            username='admin_test',
            password=self.correct_password,
            email='admin_test@wetter.com'
        )

    def test_login(self):
        # Test GET
        response = self.client.get(LOGIN_URL, {
            'username': self.user.username,
            'password': self.correct_password
        })
        self.assertEqual(response.status_code, 405)

        # Test password not match
        response = self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'wrong password'
        })

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['message'], 'Username and password does not match.')

        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], False)

        # Test user empty
        response = self.client.post(LOGIN_URL, {
            'password': 'wrong password'
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['message'], 'Please check input.')
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], False)

        # positive login
        response = self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': self.correct_password
        })

        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.data['user'], None)
        self.assertEqual(response.data['user']['username'], self.user.username)
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)

    def test_logout(self):
        response = self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': self.correct_password
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user']['username'], self.user.username)

        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)

        # Test Get
        response = self.client.get(LOGOUT_URL)
        self.assertEqual(response.status_code, 405)

        # Positive test
        response = self.client.post(LOGOUT_URL)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], False)

    def test_signup(self):
        new_user = {
            'username': 'someone',
            'password': 'goodpassword',
            'email': "someone@wetter.com"
        }
        # Test Get
        response = self.client.get(SIGNUP_URL, new_user)
        self.assertEqual(response.status_code, 405)

        # Test invalid email
        response = self.client.post(SIGNUP_URL, {
            'username': 'someone',
            'password': 'goodpassword',
            'email': "notgoodemail.com"
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['errors']['email'][0], "Enter a valid email address.")

        # Test user too long
        response = self.client.post(SIGNUP_URL, {
            'username': 'loooooooooonnnnnnnnnnngusername',
            'password': 'goodpassword',
            'email': "notgoodemail.com"
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['errors']['username'][0], "Ensure this field has no more than 20 characters.")

        # Test password too short
        response = self.client.post(SIGNUP_URL, {
            'username': 'someone',
            'password': 'abc',
            'email': "notgoodemail.com"
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['errors']['password'][0], "Ensure this field has at least 6 characters.")

        # Positive test
        response = self.client.post(SIGNUP_URL, new_user)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['username'], "someone")
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)
