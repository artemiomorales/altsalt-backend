from storages.backends.s3boto3 import S3Boto3Storage
from django.utils.encoding import (
    filepath_to_uri
)
import datetime


class MediaStorage(S3Boto3Storage):

    def url(self, name, parameters=None, expire=None):
        # Preserve the trailing slash after normalizing the path.
        name = self._normalize_name(self._clean_name(name))
        if self.custom_domain:
            return "{}//{}/{}".format(self.url_protocol,
                                      self.custom_domain, filepath_to_uri(name))
        if expire is None:
            expire = self.querystring_expire

        params = parameters.copy() if parameters else {}
        params['Bucket'] = self.bucket.name
        params['Key'] = self._encode_name(name)
        url = self.bucket.meta.client.generate_presigned_url('get_object', Params=params,
                                                             ExpiresIn=expire)
        url = (url + "&timestamp={0}").format(datetime.datetime.now().strftime("%f"))
        if self.querystring_auth:
            return url
        return self._strip_signing_parameters(url)