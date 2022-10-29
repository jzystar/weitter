from testing.testcases import TestCase

LIKE_BASE_URL = '/api/likes/'
LIKE_CANCEL_URL = '/api/likes/cancel/'
COMMENT_LIST_API = '/api/comments/'
WEIT_LIST_API = '/api/weits/'
WEIT_DETAIL_API = '/api/weits/{}/'
NEWSFEED_LIST_API = '/api/newsfeeds/'

class LikeApiTests(TestCase):

    def setUp(self):
        self.clear_cache()
        self.user1, self.user1_client = self.create_user_and_client('user1')
        self.user2, self.user2_client = self.create_user_and_client('user2')

    def test_weit_likes(self):
        weit = self.create_weit(self.user1)
        data = {'content_type': 'weit', 'object_id': weit.id}

        # test anonymous
        response = self.anonymous_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 403)
        # test get method
        response = self.user1_client.get(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 405)

        # test content type
        response = self.user1_client.post(LIKE_BASE_URL, {
            'content_type': 'wrong',
            'object_id': weit.id,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('content_type' in response.data['errors'], True)

        # test object_id
        response = self.user1_client.post(LIKE_BASE_URL, {
            'content_type': 'weit',
            'object_id': -1,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('object_id' in response.data['errors'], True)

        # positive
        response = self.user1_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(weit.like_set.count(), 1)

        # duplicated like
        self.user1_client.post(LIKE_BASE_URL, data)
        self.assertEqual(weit.like_set.count(), 1)
        self.user2_client.post(LIKE_BASE_URL, data)
        self.assertEqual(weit.like_set.count(), 2)

    def test_comment_likes(self):
        weit = self.create_weit(self.user1)
        comment = self.create_comment(self.user1, weit)
        data = {'content_type': 'comment', 'object_id': comment.id}

        # test anonymous
        response = self.anonymous_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 403)

        # test get method
        response = self.user1_client.get(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 405)

        # test content type
        response = self.user1_client.post(LIKE_BASE_URL, {
            'content_type' : 'wrong',
            'object_id': comment.id,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('content_type' in response.data['errors'], True)

        # test object_id
        response = self.user1_client.post(LIKE_BASE_URL, {
            'content_type': 'comment',
            'object_id': -1,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('object_id' in response.data['errors'], True)

        # positive
        response = self.user1_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(comment.like_set.count(), 1)

        # duplicated like
        self.user1_client.post(LIKE_BASE_URL, data)
        self.assertEqual(comment.like_set.count(), 1)
        self.user2_client.post(LIKE_BASE_URL, data)
        self.assertEqual(comment.like_set.count(), 2)

    def test_cancel(self):
        weit = self.create_weit(self.user1)
        comment = self.create_comment(self.user1, weit)
        like_comment_data = {'content_type': 'comment', 'object_id': comment.id}
        like_weit_data = {'content_type': 'weit', 'object_id': weit.id}
        self.user1_client.post(LIKE_BASE_URL, like_comment_data)
        self.user2_client.post(LIKE_BASE_URL, like_weit_data)
        self.assertEqual(comment.like_set.count(), 1)
        self.assertEqual(weit.like_set.count(), 1)

        # test auth
        response = self.anonymous_client.post(LIKE_CANCEL_URL, like_comment_data)
        self.assertEqual(response.status_code, 403)

        # test get
        response = self.user1_client.get(LIKE_CANCEL_URL, like_comment_data)
        self.assertEqual(response.status_code, 405)

        # wrong content type
        response = self.user1_client.post(LIKE_CANCEL_URL, {
            'content_type': 'wrong',
            'object_id': comment.id,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('content_type' in response.data['errors'], True)

        # test object_id
        response = self.user1_client.post(LIKE_CANCEL_URL, {
            'content_type': 'comment',
            'object_id': -1,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('object_id' in response.data['errors'], True)

        # comment not liked before
        response = self.user2_client.post(LIKE_CANCEL_URL, like_comment_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 0)
        self.assertEqual(comment.like_set.count(), 1)
        self.assertEqual(weit.like_set.count(), 1)

        # weit not liked before
        response = self.user1_client.post(LIKE_CANCEL_URL, like_weit_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 0)
        self.assertEqual(comment.like_set.count(), 1)
        self.assertEqual(weit.like_set.count(), 1)

        # positive test
        response = self.user1_client.post(LIKE_CANCEL_URL, like_comment_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 1)
        self.assertEqual(comment.like_set.count(), 0)
        self.assertEqual(weit.like_set.count(), 1)

        response = self.user2_client.post(LIKE_CANCEL_URL, like_weit_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 1)
        self.assertEqual(comment.like_set.count(), 0)
        self.assertEqual(weit.like_set.count(), 0)

    def test_likes_in_comments_api(self):
        weit = self.create_weit(self.user1)
        comment = self.create_comment(self.user1, weit)

        # test anonymous
        response = self.anonymous_client.get(COMMENT_LIST_API, {'weit_id': weit.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['comments'][0]['has_liked'], False)
        self.assertEqual(response.data['comments'][0]['likes_count'], 0)

        # test comments list
        response = self.user2_client.get(COMMENT_LIST_API, {'weit_id': weit.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['comments'][0]['has_liked'], False)
        self.assertEqual(response.data['comments'][0]['likes_count'], 0)

        self.create_like(self.user2, comment)
        response = self.user2_client.get(COMMENT_LIST_API, {'weit_id': weit.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['comments'][0]['has_liked'], True)
        self.assertEqual(response.data['comments'][0]['likes_count'], 1)

        # test weit detail api
        self.create_like(self.user1, comment)
        url = WEIT_DETAIL_API.format(weit.id)
        response = self.user2_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['comments'][0]['has_liked'], True)
        self.assertEqual(response.data['comments'][0]['likes_count'], 2)

    def test_likes_in_weits_api(self):
        weit = self.create_weit(self.user1)

        # test weit detail page
        url = WEIT_DETAIL_API.format(weit.id)
        response = self.user2_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['has_liked'], False)
        self.assertEqual(response.data['likes_count'], 0)
        self.create_like(self.user2, weit)
        response = self.user2_client.get(url)
        self.assertEqual(response.data['has_liked'], True)
        self.assertEqual(response.data['likes_count'], 1)

        # test weit list api

        response = self.user2_client.get(WEIT_LIST_API, {'user_id': self.user1.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['has_liked'], True)
        self.assertEqual(response.data['results'][0]['likes_count'], 1)

        # test newsfeed api
        self.create_like(self.user1, weit)
        self.create_newsfeed(self.user2, weit)
        response = self.user2_client.get(NEWSFEED_LIST_API)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['weit']['has_liked'], True)
        self.assertEqual(response.data['results'][0]['weit']['likes_count'], 2)

        # test like details
        url = WEIT_DETAIL_API.format(weit.id)
        response = self.user2_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['likes'][0]['user']['id'], self.user1.id)
        self.assertEqual(response.data['likes'][1]['user']['id'], self.user2.id)

