from testing.testcases import TestCase


class CommentModelTests(TestCase):

    def setUp(self):
        self.user = self.create_user(username="weittester")
        self.weit = self.create_weit(user=self.user)
        self.comment = self.create_comment(user=self.user, weit=self.weit)

    def test_comment(self):
        self.assertNotEqual(self.comment.__str__(), None)

    def test_like_set(self):
        self.create_like(self.user, self.comment)
        self.assertEqual(self.comment.like_set.count(), 1)
        self.create_like(self.user, self.comment)
        self.assertEqual(self.comment.like_set.count(), 1)

        user2 = self.create_user(username='user2')
        self.create_like(user2, self.comment)
        self.assertEqual(self.comment.like_set.count(), 2)


