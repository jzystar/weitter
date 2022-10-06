from testing.testcases import TestCase
from rest_framework.test import APIClient
from django.utils import timezone
from comments.models import Comment

COMMENT_URL = '/api/comments/'
COMMENT_DETAIL_URL = '/api/comments/{}/'

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

    def test_destroy(self):
        comment = self.create_comment(self.user1, self.weit)
        url = COMMENT_DETAIL_URL.format(comment.id)
        # anonymous
        response = self.anonymous_client.delete(url)
        self.assertEqual(response.status_code, 403)

        # test owner
        response = self.user2_client.delete(url)
        self.assertEqual(response.status_code, 403)

        #positive test
        count = Comment.objects.count()
        response = self.user1_client.delete(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), count - 1)

    def test_update(self):
        comment = self.create_comment(self.user1, self.weit)
        url = COMMENT_DETAIL_URL.format(comment.id)

        # anonymous test
        response = self.anonymous_client.put(url, {'content': 'updated'})
        self.assertEqual(response.status_code, 403)

        # test owner
        response = self.user2_client.put(url, {'content': 'updated'})
        self.assertEqual(response.status_code, 403)
        comment.refresh_from_db()
        self.assertNotEqual(comment.content, 'updated')

        # test other fields
        before_updated_at = comment.updated_at
        before_created_at = comment.created_at
        now = timezone.now()
        response = self.user1_client.put(url, {
            'content': 'updated',
            'user_id': self.user2.id,
            'weit_id': self.weit.id + 1,
            'created_at': now,
        })
        self.assertEqual(response.status_code, 200)
        # important here, need to fresh the comment data from db
        comment.refresh_from_db()
        self.assertEqual(comment.user, self.user1)
        self.assertEqual(comment.weit_id, self.weit.id)
        self.assertEqual(comment.created_at, before_created_at)
        self.assertNotEqual(comment.created_at, now)
        self.assertNotEqual(comment.updated_at, before_updated_at)



