from io import BytesIO
from django.core.files.base import ContentFile
from datetime import datetime

DEFAULT_IMAGE_SIZE_NAME = 'original'

DEFAULT_THUMBNAIL_SIZES = [
    {'attribute': 'large', 'suffix': '-1x'},
    {'attribute': 'medium', 'suffix': '-1x'},
    {'attribute': 'small', 'suffix': '-1x'},
]

RESPONSIVE_SIZES = [2, 3, 4]


def get_image_buffer(original_image_data, image_format, create_copy=False):
    if create_copy is True:
        image_instance = original_image_data.copy()
    else:
        image_instance = original_image_data

    copied_buffer = BytesIO()
    image_instance.save(fp=copied_buffer, format=image_format, optimize=True)
    return ContentFile(copied_buffer.getvalue())


def get_date_from_string(datestring):
    year = datestring[0:4]
    month = datestring[4:6]
    day = datestring[6:8]
    return datetime.fromisoformat('{0}-{1}-{2}'.format(year, month, day))
