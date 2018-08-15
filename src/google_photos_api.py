import subprocess

import requests


GOOGLE_PHOTOS_API_PAGE_SIZE = 100


class GoogleCredentialsProvider(object):
    @staticmethod
    def get_access_token(credentials_file, auth_scopes):
        """
        Generate/fetch the API tokens needed to do the actions defined in
        auth_scopes for the application/service defined in the credentials file.
        """
        # Google didn't make oauth2l an easy to use lib, so just yolo with 
        #   subprocess
        proc = subprocess.Popen(
            ['oauth2l', 'fetch', '--json', credentials_file, '-f', 'bare'] + auth_scopes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        stdout, stderr = proc.communicate()
        if proc.returncode:
            raise Exception('Failed to get Google access token.\n{}'.format(stdout))

        return stdout.strip()


class GooglePhotosAPI(object):
    @staticmethod
    def _get_images(api_token, page_token=None):
        params = {
            'pageSize': GOOGLE_PHOTOS_API_PAGE_SIZE
        }
        if page_token:
            params['pageToken'] = page_token

        return requests.get(
            'https://photoslibrary.googleapis.com/v1/mediaItems',
            headers={'Authorization': 'Bearer {}'.format(api_token)},
            params=params
        )

    @staticmethod
    def enumerate_images(api_token):
        """
        Enumerate over all images that the provided credentials allow for,
        yielding one Python dictionary for each Google Photos Media Item.
        """
        rv = GooglePhotosAPI._get_images(api_token)

        pagination_token = 1
        while pagination_token:
            global rv
            response_json = rv.json()
            pagination_token = response_json['nextPageToken']
            media_items = response_json['mediaItems']

            for media_item in media_items:
                yield media_item

            rv = GooglePhotosAPI._get_images(api_token, pagination_token)


