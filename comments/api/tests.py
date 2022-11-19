from comments.models import Comment
from django.utils import timezone
from rest_framework.test import APIClient
from testing.testcases import TestCase

COMMENT_URL = '/api/comments/'
COMMENT_DETAIL_URL = '/api/comments/{}/'
WEIT_LIST_API = '/api/weits/'
WEIT_DETAIL_API = '/api/weits/{}/'
NEWSFEED_LIST_API = '/api/newsfeeds/'


class CommentApiTests(TestCase):
    def setUp(self):
        super(CommentApiTests, self).setUp()
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

    def test_list(self):
        # not with weit_id
        response = self.anonymous_client.get(COMMENT_URL)
        self.assertEqual(response.status_code, 400)

        # positive test
        response = self.anonymous_client.get(COMMENT_URL, {
            'weit_id': self.weit.id,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['comments']), 0)

        self.create_comment(self.user1, self.weit, '1')
        self.create_comment(self.user2, self.weit, '2')
        self.create_comment(self.user2, self.create_weit(self.user2), '3')

        response = self.anonymous_client.get(COMMENT_URL, {
            'weit_id': self.weit.id,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['comments']), 2)
        self.assertEqual(response.data['comments'][0]['content'], '1')
        self.assertEqual(response.data['comments'][1]['content'], '2')
        # test add user_id param
        response = self.anonymous_client.get(COMMENT_URL, {
            'weit_id': self.weit.id,
            'user_id': self.user1.id,
        })
        self.assertEqual(len(response.data['comments']), 2)

    def test_comment_count(self):
        # test weit detail api
        weit = self.create_weit(self.user1)
        url = WEIT_DETAIL_API.format(weit.id)
        response = self.user2_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['comments_count'], 0)

        # test weit list api
        self.create_comment(self.user1, weit)
        response = self.user2_client.get(WEIT_LIST_API, {'user_id': self.user1.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['comments_count'], 1)

        # test newsfeeds list api
        self.create_comment(self.user2, weit)
        self.create_newsfeed(self.user2, weit)
        response = self.user2_client.get(NEWSFEED_LIST_API)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['weit']['comments_count'], 2)

    def test_comments_count_with_cache(self):
        weit_url = WEIT_DETAIL_API.format(self.weit.id)
        response = self.user1_client.get(weit_url)
        self.assertEqual(self.weit.comments_count, 0)
        self.assertEqual(response.data['comments_count'], 0)

        data = {'weit_id': self.weit.id, 'content': 'a comment'}
        for i in range(2):
            _, client = self.create_user_and_client('user{}'.format(i))
            client.post(COMMENT_URL, data)
            response = client.get(weit_url)
            self.assertEqual(response.data['comments_count'], i + 1)
            self.weit.refresh_from_db()
            self.assertEqual(self.weit.comments_count, i + 1)

        comment_data = self.user2_client.post(COMMENT_URL, data).data
        response = self.user2_client.get(weit_url)
        self.assertEqual(response.data['comments_count'], 3)
        self.weit.refresh_from_db()
        self.assertEqual(self.weit.comments_count, 3)

        # update comment shouldn't update comments_count
        comment_url = COMMENT_DETAIL_URL.format(comment_data['id'])
        response = self.user2_client.put(comment_url, {'content': 'updated comment'})
        self.assertEqual(response.status_code, 200)
        response = self.user2_client.get(weit_url)
        self.assertEqual(response.data['comments_count'], 3)
        self.weit.refresh_from_db()
        self.assertEqual(self.weit.comments_count, 3)

        # delete a comment will update comments_count
        response = self.user2_client.delete(comment_url)
        self.assertEqual(response.status_code, 200)
        response = self.user1_client.get(weit_url)
        self.assertEqual(response.data['comments_count'], 2)
        self.weit.refresh_from_db()
        self.assertEqual(self.weit.comments_count, 2)

