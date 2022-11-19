from inbox.services import NotificationService
from notifications.models import Notification
from testing.testcases import TestCase

COMMENT_URL = '/api/comments/'
LIKE_URL = '/api/likes/'
NOTIFICATION_URL_BASE = '/api/notifications/'
NOTIFICATION_URL_UNREAD = '/api/notifications/unread-count/'
NOTIFICATION_URL_MARKED = '/api/notifications/mark-all-as-read/'


class NotificationTests(TestCase):

    def setUp(self):
        super(NotificationTests, self).setUp()
        self.user1, self.user1_client = self.create_user_and_client('user1')
        self.user2, self.user2_client = self.create_user_and_client('user2')
        self.user2_weit = self.create_weit(self.user2)

    def test_comment_create_api_trigger_notification(self):
        self.assertEqual(Notification.objects.count(), 0)
        self.user1_client.post(COMMENT_URL, {
            'weit_id': self.user2_weit.id,
            'content': "test content",
        })
        self.assertEqual(Notification.objects.count(), 1)

    def test_like_create_api_trigger_notification(self):
        self.assertEqual(Notification.objects.count(), 0)
        self.user1_client.post(LIKE_URL, {
            'object_id': self.user2_weit.id,
            'content_type': "weit",
        })
        self.assertEqual(Notification.objects.count(), 1)


class NotificationApiTests(TestCase):
    def setUp(self):
        self.user1, self.user1_client = self.create_user_and_client('user1')
        self.user2, self.user2_client = self.create_user_and_client('user2')
        self.user1_weit = self.create_weit(self.user1)

    def test_unread_count(self):
        response = self.user2_client.post(LIKE_URL, {
            'content_type': 'weit',
            'object_id': self.user1_weit.id,
        })
        self.assertEqual(response.status_code, 201)

        response = self.user1_client.get(NOTIFICATION_URL_UNREAD)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['unread_count'], 1)

        comment = self.create_comment(self.user1, self.user1_weit)
        self.user2_client.post(LIKE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })
        response = self.user1_client.get(NOTIFICATION_URL_UNREAD)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['unread_count'], 2)

        response = self.user2_client.get(NOTIFICATION_URL_UNREAD)
        self.assertEqual(response.data['unread_count'], 0)

    def test_mark_all_as_read(self):
        self.user2_client.post(LIKE_URL, {
            'content_type': 'weit',
            'object_id': self.user1_weit.id,
        })
        comment = self.create_comment(self.user1, self.user1_weit)
        self.user2_client.post(LIKE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })
        response = self.user1_client.get(NOTIFICATION_URL_UNREAD)
        self.assertEqual(response.data['unread_count'], 2)

        response = self.user1_client.get(NOTIFICATION_URL_MARKED)
        self.assertEqual(response.status_code, 405)

        response = self.user2_client.post(NOTIFICATION_URL_MARKED)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['marked_count'], 0)
        response = self.user1_client.get(NOTIFICATION_URL_UNREAD)
        self.assertEqual(response.data['unread_count'], 2)

        response = self.user1_client.post(NOTIFICATION_URL_MARKED)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['marked_count'], 2)
        response = self.user1_client.get(NOTIFICATION_URL_UNREAD)
        self.assertEqual(response.data['unread_count'], 0)

    def test_list(self):
        self.user2_client.post(LIKE_URL, {
            'content_type': 'weit',
            'object_id': self.user1_weit.id,
        })
        comment = self.create_comment(self.user1, self.user1_weit)
        self.user2_client.post(LIKE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })

        response = self.anonymous_client.get(NOTIFICATION_URL_BASE)
        self.assertEqual(response.status_code, 403)

        response = self.user2_client.get(NOTIFICATION_URL_BASE)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

        response = self.user1_client.get(NOTIFICATION_URL_BASE)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)

        # mark one as read
        notification = self.user1.notifications.first()
        notification.unread = False
        notification.save()
        response = self.user1_client.get(NOTIFICATION_URL_BASE)
        self.assertEqual(response.data['count'], 2)
        response = self.user1_client.get(NOTIFICATION_URL_BASE, {'unread': True})
        self.assertEqual(response.data['count'], 1)
        response = self.user1_client.get(NOTIFICATION_URL_BASE, {'unread': False})
        self.assertEqual(response.data['count'], 1)

    def test_update(self):
        self.user2_client.post(LIKE_URL, {
            'content_type': 'weit',
            'object_id': self.user1_weit.id,
        })
        comment = self.create_comment(self.user1, self.user1_weit)
        self.user2_client.post(LIKE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })

        notification = self.user1.notifications.first()
        url = NOTIFICATION_URL_BASE + '{}/'.format(notification.id)

        response = self.user1_client.post(url, {'unread': False})
        self.assertEqual(response.status_code, 405)

        response = self.anonymous_client.put(url, {'unread': False})
        self.assertEqual(response.status_code, 403)

        response = self.user2_client.put(url, {'unread': False})
        self.assertEqual(response.status_code, 404)

        response = self.user1_client.put(url, {'unread': False})
        self.assertEqual(response.status_code, 200)
        response = self.user1_client.get(NOTIFICATION_URL_UNREAD)
        self.assertEqual(response.data['unread_count'], 1)

        response = self.user1_client.put(url, {'unread': True})
        self.assertEqual(response.status_code, 200)
        response = self.user1_client.get(NOTIFICATION_URL_UNREAD)
        self.assertEqual(response.data['unread_count'], 2)

        response = self.user1_client.put(url, {'verb': 'test'})
        self.assertEqual(response.status_code, 400)

        response = self.user1_client.put(url, {'unread': True, 'verb': 'test'})
        self.assertEqual(response.status_code, 200)
        notification.refresh_from_db()
        self.assertNotEqual(notification.verb, 'test')




