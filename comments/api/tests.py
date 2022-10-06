from testing.testcases import TestCase
from rest_framework.test import APIClient

COMMENT_URL = '/api/comments/'


class CommentApiTests(TestCase):
    def setUp(self):
        self.user1 = self.create_user('testuser1')
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)
        self.user2 = self.create_user('testuser2')
        self.user2_client = APIClient()
        self.user2_client.force_authenticate(self.user2)
        self.weit = self.create_weit(self.user1)

    def test_create(self):
        # test authentication
        response = self.anonymous_client.post(COMMENT_URL)
        self.assertEqual(response.status_code, 403)

        # test no data in body
        response = self.user1_client.post(COMMENT_URL)
        self.assertEqual(response.status_code, 400)

        # test no content
        response = self.user1_client.post(COMMENT_URL, {'weit_id': self.weit.id})
        self.assertEqual(response.status_code, 400)

        # test no weit_id
        response = self.user1_client.post(COMMENT_URL, {'content': 'test content'})
        self.assertEqual(response.status_code, 400)

        # content length
        response = self.user1_client.post(
            COMMENT_URL,
            {'content': '1' * 141, 'weit_id':self.weit.id}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual('content' in response.data['errors'], True)

        # positive test
        response = self.user1_client.post(
            COMMENT_URL,
            {'content': 'test content', 'weit_id': self.weit.id}
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['id'], self.user1.id)
        self.assertEqual(response.data['weit_id'], self.weit.id)
        self.assertEqual(response.data['content'], 'test content')

