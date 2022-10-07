from testing.testcases import TestCase

LIKE_BASE_URL = '/api/likes/'
class LikeApiTests(TestCase):

    def setUp(self):
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



