"""
Helper functions for the Organization themes API.
"""
import hashlib
from contextlib import closing
from io import BytesIO as StringIO

from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.files.base import ContentFile
from django.core.files.storage import get_storage_class
from edx_solutions_api_integration.utils import prefix_with_lms_base
from openedx.core.djangoapps.profile_images.images import _get_corrected_exif
from PIL import Image

IMAGE_FILE_EXTENSION = 'jpg'   # All processed images are converted to JPEGs
IMAGE_KEY_PREFIX = 'image_url'


def get_image_storage(config):
    """
    Configures and returns a django Storage instance that can be used
    to physically locate, read and write images.
    """
    storage_class = get_storage_class(config['class'])
    return storage_class(**config['options'])


def _make_image_name(secret_key, custom_key):
    """
    Returns the key-specific part of the image filename, based on a hash of
    the key.
    """
    hash_input = secret_key + custom_key
    return hashlib.md5(hash_input.encode('utf-8')).hexdigest()


def _get_image_filename(name, size, file_extension=IMAGE_FILE_EXTENSION):
    """
    Returns the full filename for an image, given the name and size.
    """
    return '{name}_{size}.{file_extension}'.format(name=name, size=size, file_extension=file_extension)


def _get_image_urls(name, sizes, storage, file_extension=IMAGE_FILE_EXTENSION, version=None):
    """
    Returns a dict containing the urls for a complete set of images,
    keyed by "friendly" name (e.g. "full", "large", "medium", "small", "x-small").
    """
    def _make_url(size):  # pylint: disable=missing-docstring
        url = storage.url(
            _get_image_filename(name, size, file_extension=file_extension)
        )
        return '{}?v={}'.format(url, version) if version is not None else url

    return {
        size_display_name: _make_url(size)
        for size_display_name, size in sizes.items()
    }


def get_image_names(secret_key, custom_key, image_sizes):
    """
    Returns a dict containing the filenames for a complete set of images, keyed by pixel size.
    """
    name = _make_image_name(secret_key, custom_key)
    return {size: _get_image_filename(name, size) for size in image_sizes}


def _get_default_image_urls(default_filename, sizes):
    """
    Returns a dict {size:url} for a complete set of default images,
    used as a placeholder when there are no user-submitted images.

    #TODO The result of this function should be memoized, but not in tests.
    """
    return _get_image_urls(
        default_filename,
        sizes,
        staticfiles_storage,
        file_extension=settings.IMAGE_DEFAULT_FILE_EXTENSION,
    )


def set_has_logo_image(theme, is_uploaded, upload_dt=None):
    """
    System (not user-facing) API call used to store whether the organization has an
    uploaded logo image, and if so, when.  Used by organization themes API.

    Arguments:
        organization_id: id of the organization
        is_uploaded (bool): whether or not the user has an uploaded logo image.
        upload_dt (datetime.datetime): If `is_uploaded` is True, this should
            contain the server-side date+time of the upload.  If `is_uploaded`
            is False, the parameter is optional and will be ignored.

    Raises:
        ValueError: is_uploaded was True, but no upload datetime was supplied.
        OrganizationNotFound: no active organization with this id exists.
    """
    if is_uploaded and upload_dt is None:
        raise ValueError("No upload datetime was supplied.")
    elif not is_uploaded:
        upload_dt = None

    theme.logo_image_uploaded_at = upload_dt
    theme.save()


def create_images(image_file, image_names, image_backend):
    """
    Generates a set of image files based on image_file and stores them
    according to the sizes and filenames specified in `image_names`.

    Arguments:
        image_file (file):
            The uploaded image file to be scaled.
        image_names (dict):
            A dictionary that maps image sizes to file names. The image size
            is an integer representing one side of the equilateral image to be
            created.
        image_backend (dict):
            A dictionary that contains image storage and other location options
            for the creating images.
    Returns:
        None
    """
    storage = get_image_storage(image_backend)
    original = Image.open(image_file)
    original_format = original.format
    image = _set_color_mode_to_rgba(original)
    for size, name in image_names.items():
        size = size.split('x')
        scaled = _scale_image(image, int(size[0]), int(size[1]))
        exif = _get_corrected_exif(scaled, original)
        with closing(_create_image_file(scaled, exif, original_format)) as scaled_image_file:
            storage.save(name, scaled_image_file)


def remove_images(image_backend, image_names):
    """
    Physically remove the image files specified in `image_names`
    """
    storage = get_image_storage(image_backend)
    for name in image_names.values():
        storage.delete(name)


def get_image_urls_by_key(
        secret_key,
        custom_key,
        image_uploaded_at,
        images_sizes,
        image_storage,
        is_default_required,
        default_filename=None,
):
    """
    Return a dict {size:url} for each image for a given key.

    Arguments:
        secret_key:  secret key for whom we are getting urls.
        custom_key:  custom key for whom we are getting urls.
        image_uploaded_at:  image uploaded at value.
        images_sizes:  image size dict.
        image_storage:  storage for images.
        is_default_required:  whether one need default images or not.
        default_filename:  if default images are required then what will be its name.

    Returns:
        dictionary of {size_display_name: url} for each image.
    """
    urls = {}
    data = {'has_image': True if image_uploaded_at else False}
    if image_uploaded_at:
        urls = _get_image_urls(
            _make_image_name(secret_key, custom_key),
            images_sizes,
            get_image_storage(image_storage),
            version=image_uploaded_at.strftime("%s"),
        )
    elif is_default_required:
        urls = _get_default_image_urls(default_filename, images_sizes)
        urls = {size_display_name: prefix_with_lms_base(url) for size_display_name, url in urls.items()}
    data.update({
        '{image_key_prefix}_{size}'.format(
            image_key_prefix=IMAGE_KEY_PREFIX,
            size=size_display_name): url
        for size_display_name, url in urls.items()
    })
    return data


def _scale_image(image, side_length, side_width):
    """
    Given a PIL.Image object, get a resized copy having width equals `side_width` pixels
    and length `side_length` pixels.
    """
    resized_image = image.resize((side_length, side_width), Image.ANTIALIAS)
    return resized_image


def _set_color_mode_to_rgba(image):
    """
    Given a PIL.Image object, return a copy with the color mode set to RGBA.
    """
    return image.convert('RGBA')


def _create_image_file(image, exif, format):
    """
    Given a PIL.Image object, create and return a file-like object containing
    the data saved in given format.

    Note that the file object returned is a django ContentFile which holds data
    in memory (not on disk).
    """
    string_io = StringIO()

    # The if/else dance below is required, because PIL raises an exception if
    # you pass None as the value of the exif kwarg.
    if exif is None:
        image.save(string_io, format=format)
    else:
        image.save(string_io, format=format, exif=exif)

    image_file = ContentFile(string_io.getvalue())
    return image_file
