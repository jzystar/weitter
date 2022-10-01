from weits.models import Weit
from testing.testcases import TestCase
from rest_framework.test import APIClient

WEIT_LIST_API = '/api/weits/'
WEIT_CREATE_API = '/api/weits/'

class WeitApiTests(TestCase):

    def setUp(self):
        self.anonymous_client = APIClient()

        self.user1 = self.create_user('user1', 'user1@weitter.com')
        self.weits1 = [
            self.create_weit(self.user1, f'{self.user1.username} post {i} content')
            for i in range(3)
        ]

        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)

        self.user2 = self.create_user('user2', 'user2@weitter.com')
        self.weits2 = [
            self.create_weit(self.user2) for i in range(2)
        ]

    def test_list_api(self):
        # not with user id
        reponse = self.anonymous_client.get(WEIT_LIST_API)
        self.assertEqual(reponse.status_code, 400)

        # regular rquest
        response = self.anonymous_client.get(WEIT_LIST_API, {'user_id': self.user1.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['weits']), 3)
        response = self.anonymous_client.get(WEIT_LIST_API, {'user_id': self.user2.id})
        self.assertEqual(len(response.data['weits']), 2)

        # test order
        self.assertEqual(response.data['weits'][0]['id'], self.weits2[1].id)
        self.assertEqual(response.data['weits'][1]['id'], self.weits2[0].id)

    def test_create_api(self):
        # test login validation
        response = self.anonymous_client.post(WEIT_CREATE_API)
        self.assertEqual(response.status_code, 403)

        # test no content
        response = self.user1_client.post(WEIT_CREATE_API)
        self.assertEqual(response.status_code, 400)

        # test content length
        response = self.user1_client.post(WEIT_CREATE_API, {'content': "1"})
        self.assertEqual(response.status_code, 400)
        response = self.user1_client.post(WEIT_CREATE_API, {
            'content': "1" * 141
        })
        self.assertEqual(response.status_code, 400)

        # positive test
        count = Weit.objects.count()
        response = self.user1_client.post(WEIT_CREATE_API, {
            'content': 'positive test content'
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['id'], self.user1.id)
        self.assertEqual(Weit.objects.count(), count + 1)




