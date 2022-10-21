class WeitPhotoStatus:
    PENDING = 0
    APPROVED = 1
    REJECTED = 2


WEIT_PHOTO_STATUS_CHOICES = (
    (WeitPhotoStatus.PENDING, 'Pending'),
    (WeitPhotoStatus.APPROVED, 'Approved'),
    (WeitPhotoStatus.REJECTED, 'Rejected'),
)

WEIT_PHOTOS_UPLOAD_LIMIT = 9
