from testing.testcases import  TestCase

class CommentModelTests(TestCase):

    def test_comment(self):
        user = self.create_user(username="weittester")
        weit = self.create_weit(user=user)
        comment = self.create_comment(user=user, weit=weit)
        self.assertNotEqual(comment.__str__(), None)

