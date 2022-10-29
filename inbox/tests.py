from inbox.services import NotificationService
from notifications.models import Notification
from testing.testcases import TestCase


class NotificationServiceTests(TestCase):

    def setUp(self):
        self.clear_cache()
        self.user1 = self.create_user('user1')
        self.user2 = self.create_user('user2')
        self.user1_weit = self.create_weit(self.user1)

    def test_send_like_notification(self):
        like = self.create_like(self.user1, self.user1_weit)
        NotificationService.send_like_notification(like)
        self.assertEqual(Notification.objects.count(), 0)

        like = self.create_like(self.user2, self.user1_weit)
        NotificationService.send_like_notification(like)
        self.assertEqual(Notification.objects.count(), 1)

    def test_send_comment_notification(self):
        comment = self.create_comment(self.user1, self.user1_weit)
        NotificationService.send_comment_notification(comment)
        self.assertEqual(Notification.objects.count(), 0)

        comment = self.create_comment(self.user2, self.user1_weit)
        NotificationService.send_comment_notification(comment)
        self.assertEqual(Notification.objects.count(), 1)