from weits.models import Weit, WeitPhoto

class WeitService(object):

    @classmethod
    def create_photos_from_files(cls, weit, files):
        photos = []
        for index, file in enumerate(files):
            photo = WeitPhoto(
                weit=weit,
                user=weit.user,
                file=file,
                order=index,
            )
            photos.append(photo)
        WeitPhoto.objects.bulk_create(photos)
