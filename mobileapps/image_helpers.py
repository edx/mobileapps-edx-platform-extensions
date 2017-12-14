"""
Helper functions for the Organization themes API.
"""
import hashlib
from PIL import Image
from contextlib import closing

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import get_storage_class
from django.contrib.staticfiles.storage import staticfiles_storage

from edx_solutions_api_integration.utils import prefix_with_lms_base

from student.models import UserProfile
from openedx.core.djangoapps.profile_images.images import (
    _set_color_mode_to_rgb,
    _get_corrected_exif,
    _create_image_file,
)
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

from mobileapps.models import Theme

ORGANIZATION_LOGO_IMAGE_FILE_EXTENSION = 'jpg'   # All processed organization logo images are converted to JPEGs
ORGANIZATION_LOGO_IMAGE_KEY_PREFIX = 'image_url'
_ORGANIZATION_LOGO_IMAGE_SIZES_MAP = settings.ORGANIZATION_LOGO_IMAGE_SIZES_MAP.values()


def get_logo_image_storage():
    """
    Configures and returns a django Storage instance that can be used
    to physically locate, read and write organization logo images.
    """
    config = settings.ORGANIZATION_LOGO_IMAGE_BACKEND
    storage_class = get_storage_class(config['class'])
    return storage_class(**config['options'])


def _make_logo_image_name(key):
    """
    Returns the organization-specific part of the image filename, based on a hash of
    the organization_name.
    """
    hash_input = settings.ORGANIZATION_LOGO_IMAGE_SECRET_KEY + key
    return hashlib.md5(hash_input.encode('utf-8')).hexdigest()


def _get_logo_image_filename(name, size, file_extension=ORGANIZATION_LOGO_IMAGE_FILE_EXTENSION):
    """
    Returns the full filename for a organization logo image, given the name and size.
    """
    return '{name}_{size}.{file_extension}'.format(name=name, size=size, file_extension=file_extension)


def _get_logo_image_urls(name, storage, file_extension=ORGANIZATION_LOGO_IMAGE_FILE_EXTENSION, version=None):
    """
    Returns a dict containing the urls for a complete set of organization logo images,
    keyed by "friendly" name (e.g. "full", "large", "medium", "small", "x-small").
    """
    def _make_url(size):  # pylint: disable=missing-docstring
        url = storage.url(
            _get_logo_image_filename(name, size, file_extension=file_extension)
        )
        return '{}?v={}'.format(url, version) if version is not None else url

    return {
        size_display_name: _make_url(size)
        for size_display_name, size in settings.ORGANIZATION_LOGO_IMAGE_SIZES_MAP.items()
    }


def get_logo_image_names(key):
    """
    Returns a dict containing the filenames for a complete set of organization logo
    images, keyed by pixel size.
    """
    name = _make_logo_image_name(key)
    return {size: _get_logo_image_filename(name, size) for size in _ORGANIZATION_LOGO_IMAGE_SIZES_MAP}


def _get_default_logo_image_urls():
    """
    Returns a dict {size:url} for a complete set of default organization logo images,
    used as a placeholder when there are no user-submitted organization logo images.

    #TODO The result of this function should be memoized, but not in tests.
    """
    return _get_logo_image_urls(
        configuration_helpers.get_value(
            'ORGANIZATION_LOGO_IMAGE_DEFAULT_FILENAME',
            settings.ORGANIZATION_LOGO_IMAGE_DEFAULT_FILENAME
        ),
        staticfiles_storage,
        file_extension=settings.ORGANIZATION_LOGO_IMAGE_DEFAULT_FILE_EXTENSION,
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


def create_logo_images(image_file, logo_image_names):
    """
    Generates a set of image files based on image_file and stores them
    according to the sizes and filenames specified in `logo_image_names`.

    Arguments:
        image_file (file):
            The uploaded image file to be scaled to use as a logo image.
        logo_image_names (dict):
            A dictionary that maps image sizes to file names. The image size
            is an integer representing one side of the equilateral image to be
            created.

    Returns:
        None
    """
    storage = get_logo_image_storage()
    original = Image.open(image_file)
    image = _set_color_mode_to_rgb(original)
    for size, name in logo_image_names.items():
        size = size.split('x')
        scaled = _scale_image(image, int(size[0]), int(size[1]))
        exif = _get_corrected_exif(scaled, original)
        with closing(_create_image_file(scaled, exif)) as scaled_image_file:
            storage.save(name, scaled_image_file)


def get_logo_image_urls_by_organization_name(key, logo_image_uploaded_at):
    """
    Return a dict {size:url} for each organization logo image for a given organization.

    Arguments:
        organization_name  organization_name of organization for whom we are getting urls.
        logo_image_uploaded_at datetime when organization logo image uploaded

    Returns:
        dictionary of {size_display_name: url} for each image.
    """

    if logo_image_uploaded_at:
        urls = _get_logo_image_urls(
            _make_logo_image_name(key),
            get_logo_image_storage(),
            version=logo_image_uploaded_at.strftime("%s"),
        )
        urls = {size_display_name: prefix_with_lms_base(url) for size_display_name, url in urls.items()}
    else:
        urls = _get_default_logo_image_urls()
        urls = {size_display_name: prefix_with_lms_base(url) for size_display_name, url in urls.items()}

    data = {'has_image': True if logo_image_uploaded_at else False}
    data.update({
        '{image_key_prefix}_{size}'.format(
            image_key_prefix=ORGANIZATION_LOGO_IMAGE_KEY_PREFIX,
            size=size_display_name): url
        for size_display_name, url in urls.items()
    })
    return data


def _scale_image(image, side_length, side_width):
    """
    Given a PIL.Image object, get a resized copy with each side being
    `side_length` pixels long.  The scaled image will always be square.
    """
    return image.resize((side_length, side_width), Image.ANTIALIAS)
