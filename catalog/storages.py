"""Custom storage backends for the catalog app."""

from botocore import UNSIGNED
from botocore.client import Config

from storages.backends.s3boto3 import S3Boto3Storage


class AnonymousS3Boto3Storage(S3Boto3Storage):
    """Read/serve a public S3 bucket with unsigned (credential-free) requests.

    The ``altsalt`` bucket grants public ``s3:GetObject``, so the backend can
    read objects — e.g. to compute image dimensions during GraphQL resolution —
    without any AWS credentials. Using unsigned requests avoids depending on
    valid AWS keys or correct SigV4 region binding.

    Note: writes/uploads are not possible anonymously. If upload support is
    needed later, configure valid credentials and use the standard
    ``storages.backends.s3boto3.S3Boto3Storage`` instead.
    """

    # Providing ``config`` here makes S3Boto3Storage skip building its own and
    # use these unsigned settings (see django-storages 1.9.1 __init__).
    config = Config(signature_version=UNSIGNED)

    def _get_access_keys(self):
        return None, None

    def _get_security_token(self):
        return None
