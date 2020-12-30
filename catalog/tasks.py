from django.apps import apps
import PIL.Image as ImageUtils
from catalog.constants import DEFAULT_IMAGE_SIZE_NAME, DEFAULT_THUMBNAIL_SIZES, RESPONSIVE_SIZES, get_image_buffer
from django.core.files.uploadhandler import InMemoryUploadedFile
from catalog.backends import CatalogImageStorage
import boto3

import os
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

import logging


def clean_bucket(dry_run=True):

    from catalog.models import Listing
    from catalog.models import ListingCoverImage, ListingPreviewImage
    from catalog.models.user import User, UserProfileImage
    from catalog.models.base import catalog_media_path, profile_image_path

    storage = CatalogImageStorage()
    s3 = boto3.client('s3')

    listings = Listing.objects.all()
    users = User.objects.all()

    for listing in listings:

        logging.error("LISTING ID")
        logging.error(listing.id)
        logging.error("")

        response = s3.list_objects_v2(
            Bucket=os.environ.get('AWS_STORAGE_BUCKET_NAME'),
            Prefix=catalog_media_path('listing', listing.id)
        )

        covers = ListingCoverImage.objects.filter(listing_id=listing.id)
        previews = ListingPreviewImage.objects.filter(listing_id=listing.id)

        cover_image_names = get_image_names(covers)
        preview_image_names = get_image_names(previews)

        valid_names = cover_image_names + preview_image_names

        if "Contents" in response:
            for item in response['Contents']:
                if not item['Key'] in valid_names:
                    if dry_run:
                        logging.error(item['Key'])
                    else:
                        storage.delete(item['Key'])

        if dry_run:
            logging.error('-------------------------')

    for user in users:
        logging.error("USERNAME")
        logging.error(user.username)
        logging.error("")

        response = s3.list_objects_v2(
            Bucket=os.environ.get('AWS_STORAGE_BUCKET_NAME'),
            Prefix=catalog_media_path('user', user.id)
        )

        profile_images = UserProfileImage.objects.filter(user_id=user.id)
        profile_image_names = get_image_names(profile_images)

        if "Contents" in response:
            for item in response['Contents']:
                if not item['Key'] in profile_image_names:
                    if dry_run:
                        logging.error(item['Key'])
                    else:
                        storage.delete(item['Key'])

        if dry_run:
            logging.error('-------------------------')


def get_image_names(image_object_collection):
    image_names = []

    for image_object in image_object_collection:

        # Add default image to valid names
        default_attribute = getattr(image_object, DEFAULT_IMAGE_SIZE_NAME)
        if default_attribute is not None and default_attribute.name is not None:
            default_name = default_attribute.name
            image_names.append(default_name)

        # THUMBNAILS ARE NOT CURRENTLY IN USE
        #
        # Add thumbnails and responsive images
        # for thumbnail_size in DEFAULT_THUMBNAIL_SIZES:
        #     thumbnail_attribute = getattr(image_object, thumbnail_size['attribute'])
        #     if thumbnail_attribute is not None and thumbnail_attribute.name is not None:
        #         thumbnail_name = thumbnail_attribute.name
        #         image_names.append(thumbnail_name)
        #         for responsive_size in RESPONSIVE_SIZES:
        #             image_names.append(thumbnail_name.replace('-1x', "-{0}x".format(responsive_size)))

    return image_names


def generate_thumbnails(target_model, target_id, mime_type, filename, extension):

    storage = CatalogImageStorage()
    image_model = apps.get_model(app_label='catalog', model_name=target_model, require_ready=True)

    if image_model is not None and \
            image_model.objects.filter(id=target_id).exists() is True:

        model_instance = image_model.objects.get(id=target_id)

        # Open the original image so we can use it
        # to generate the responsive thumbnails
        original_image_attribute = getattr(model_instance, DEFAULT_IMAGE_SIZE_NAME)
        original_image_data = ImageUtils.open(original_image_attribute)

        for size in DEFAULT_THUMBNAIL_SIZES:

            # Generate and save the default image sizes
            # into the database using Django's ORM
            thumbnail_buffer = get_image_buffer(original_image_data, mime_type, True)
            thumbnail_file = InMemoryUploadedFile(thumbnail_buffer, None, filename, 'text/plain',
                                                  len(thumbnail_buffer), None, mime_type)
            thumbnail_name = "{0}-{1}{2}{3}".format(filename, size['attribute'], size['suffix'], extension)
            getattr(model_instance, size['attribute']).save(
                name=thumbnail_name,
                content=thumbnail_file,
                save=False
            )
            model_instance.save(skip_callback=True)

            # After saving the thumbnail, retrieve its width and height,
            # which we'll use to generate the responsive sizes
            thumbnail_attribute = getattr(model_instance, size['attribute'])
            target_width = thumbnail_attribute.width
            target_height = thumbnail_attribute.height

            responsive_sizes = [2, 3, 4]
            for responsive_size in responsive_sizes:

                # Identify the multiplier
                responsive_name = thumbnail_attribute.name.replace('-1x', "-{0}x".format(responsive_size))

                # Create responsive size and upload directly to S3. Note: Since we're
                # not saving these values to the database, there's no need to create
                # an InMemoryUploaded file or use Django's ORM for these generated images
                responsive_image = original_image_data.copy()
                responsive_image.thumbnail((target_width * responsive_size, target_height * responsive_size))
                responsive_buffer = get_image_buffer(responsive_image, mime_type)
                storage.save(responsive_name, responsive_buffer)