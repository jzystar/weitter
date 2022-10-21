from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from testing.testcases import TestCase
from weits.models import Weit, WeitPhoto

WEIT_LIST_API = '/api/weits/'
WEIT_CREATE_API = '/api/weits/'
WEIT_RETRIEVE_API = '/api/weits/{}/'

class WeitApiTests(TestCase):

    def setUp(self):
        #self.anonymous_client = APIClient()

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

    def test_retrieve(self):
        # weit id does not exist
        url = WEIT_RETRIEVE_API.format(-1)
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 404)

        weit = self.create_weit(self.user1)
        url = WEIT_RETRIEVE_API.format(weit.id)
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['comments']), 0)
        self.create_comment(self.user1, weit, 'comment1')
        self.create_comment(self.user2, weit, 'comment2')
        self.create_comment(self.user2, self.create_weit(self.user1), 'comment3')
        response = self.anonymous_client.get(url)
        self.assertEqual(len(response.data['comments']), 2)

    def test_create_with_files(self):
        # test no file field, compatible to old api
        response = self.user1_client.post(WEIT_CREATE_API, {
            'content': 'a test file',
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(WeitPhoto.objects.count(), 0)

        # test empty files list
        response = self.user1_client.post(WEIT_CREATE_API, {
            'content': 'a test file',
            'files': [],
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(WeitPhoto.objects.count(), 0)

        # test single file
        file = SimpleUploadedFile(
            name='testfile.jpg',
            content=str.encode('selfie 1'),
            content_type='image/jpeg',
        )
        response = self.user1_client.post(WEIT_CREATE_API, {
            'content': 'a test file',
            'files': [file],
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(WeitPhoto.objects.count(), 1)

        file1 = SimpleUploadedFile(
            name='testfile1.jpg',
            content=str.encode('selfie 1'),
            content_type='image/jpeg',
        )
        file2 = SimpleUploadedFile(
            name='testfile2.jpg',
            content=str.encode('selfie 2'),
            content_type='image/jpeg',
        )
        response = self.user1_client.post(WEIT_CREATE_API, {
            'content': 'a test file',
            'files': [file1, file2],
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(WeitPhoto.objects.count(), 3)

        # test get photo url from get
        retrieve_url = WEIT_RETRIEVE_API.format(response.data['id'])
        response = self.user1_client.get(retrieve_url)
        self.assertEqual(len(response.data['photo_urls']), 2)
        self.assertTrue('testfile1' in response.data['photo_urls'][0], True)
        self.assertTrue('testfile2' in response.data['photo_urls'][1], True)

        # test more than 9 files
        files = [
            SimpleUploadedFile(
                name=f'testfile{i}.jpg',
                content=str.encode(f'selfie {i}'),
                content_type='image/jpeg',
            )
            for i in range(10)
        ]
        response = self.user1_client.post(WEIT_CREATE_API, {
            'content': 'failed due to number of photo exceeds limit',
            'files': files,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(WeitPhoto.objects.count(), 3)






