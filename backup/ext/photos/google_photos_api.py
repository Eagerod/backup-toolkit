import copy
import os
import signal
import subprocess
import time

import requests


GOOGLE_PHOTOS_IMAGE_API_PAGE_SIZE = 100
GOOGLE_PHOTOS_ALBUM_API_PAGE_SIZE = 50


class GooglePhotosImage(object):
    def __init__(self, raw_json):
        self.json = copy.deepcopy(raw_json)

    @property
    def mime_type(self):
        return self.json['mimeType']

    @property
    def base_url(self):
        return self.json['baseUrl']

    @property
    def filename(self):
        return self.json['filename']

    @property
    def media_metadata(self):
        return self.json['mediaMetadata']

    @property
    def id(self):
        return self.json['id']


class GooglePhotosAlbum(object):
    def __init__(self, raw_json):
        self.json = copy.deepcopy(raw_json)

    @property
    def title(self):
        return self.json['title']

    @property
    def media_items_count(self):
        return self.json['mediaItemsCount']

    @property
    def id(self):
        return self.json['id']


class GoogleCredentialsProvider(object):
    @staticmethod
    def check_has_access_token(credentials_file, auth_scopes):
        """
        Give oauth2l 10 ms to respond with a credential, and if it doesn't have
        one, kill that subprocess, and start one up that will actually print out

        This is pretty sketchy, but it does work.
        """
        proc = subprocess.Popen(
            ['oauth2l', 'fetch', '--json', credentials_file, '-f', 'bare'] + auth_scopes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid
        )

        time.sleep(0.01)

        if proc.returncode is None:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            return False

        return proc.returncode == 0

    @staticmethod
    def fetch_access_token(credentials_file, auth_scopes):
        """
        Wait for the user to do the oauth flow.
        """
        proc = subprocess.Popen(
            ['oauth2l', 'fetch', '--json', credentials_file, '-f', 'bare'] + auth_scopes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        stdout, stderr = proc.communicate()
        if proc.returncode:
            raise Exception('Failed to get Google access token.\n{}'.format(stdout))

    @staticmethod
    def get_access_token(credentials_file, auth_scopes):
        """
        Generate/fetch the API tokens needed to do the actions defined in
        auth_scopes for the application/service defined in the credentials file.
        """
        # Google didn't make oauth2l an easy to use lib, so just yolo with
        #   subprocess
        if not GoogleCredentialsProvider.check_has_access_token(credentials_file, auth_scopes):
            GoogleCredentialsProvider.fetch_access_token(credentials_file, auth_scopes)

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
            'pageSize': GOOGLE_PHOTOS_IMAGE_API_PAGE_SIZE
        }
        if page_token:
            params['pageToken'] = page_token

        return requests.get(
            'https://photoslibrary.googleapis.com/v1/mediaItems',
            headers={'Authorization': 'Bearer {}'.format(api_token)},
            params=params
        )

    @staticmethod
    def _get_albums(api_token, page_token=None):
        """
        https://developers.google.com/photos/library/reference/rest/v1/albums/list
        """
        params = {
            'pageSize': GOOGLE_PHOTOS_ALBUM_API_PAGE_SIZE
        }
        if page_token:
            params['pageToken'] = page_token

        return requests.get(
            'https://photoslibrary.googleapis.com/v1/albums',
            headers={'Authorization': 'Bearer {}'.format(api_token)},
            params=params
        )

    @staticmethod
    def _get_images_from_album(api_token, album, page_token=None):
        params = {
            'pageSize': GOOGLE_PHOTOS_IMAGE_API_PAGE_SIZE,
            'albumId': album.id
        }
        if page_token:
            params['pageToken'] = page_token

        return requests.post(
            'https://photoslibrary.googleapis.com/v1/mediaItems:search',
            headers={'Authorization': 'Bearer {}'.format(api_token)},
            params=params
        )

    @staticmethod
    def enumerate_albums(api_token):
        rv = GooglePhotosAPI._get_albums(api_token)

        pagination_token = 1
        while pagination_token:
            if rv.status_code != 200:
                raise Exception(rv.text)

            response_json = rv.json()

            pagination_token = response_json.get('nextPageToken')
            media_items = response_json['albums']

            for media_item in media_items:
                yield GooglePhotosAlbum(media_item)

            if pagination_token:
                rv = GooglePhotosAPI._get_albums(api_token, pagination_token)

    @staticmethod
    def get_album(api_token, album):
        """
        https://developers.google.com/photos/library/reference/rest/v1/albums/get
        """
        return requests.get(
            'https://photoslibrary.googleapis.com/v1/albums/{}'.format(album.id),
            headers={'Authorization': 'Bearer {}'.format(api_token)}
        )

    @staticmethod
    def enumerate_images(api_token):
        """
        Enumerate over all images that the provided credentials allow for,
        yielding one GooglePhotosImage for each Google Photos Media Item.
        """
        rv = GooglePhotosAPI._get_images(api_token)

        pagination_token = 1
        while pagination_token:
            if rv.status_code != 200:
                raise Exception(rv.text)

            response_json = rv.json()

            pagination_token = response_json.get('nextPageToken')
            media_items = response_json['mediaItems']

            for media_item in media_items:
                yield GooglePhotosImage(media_item)

            if pagination_token:
                rv = GooglePhotosAPI._get_images(api_token, pagination_token)

    @staticmethod
    def enumerate_images_in_album(api_token, album):
        """
        Enumerate over all images that the provided credentials allow for,
        yielding one GooglePhotosImage for each Google Photos Media Item.
        """
        rv = GooglePhotosAPI._get_images_from_album(api_token, album)

        pagination_token = 1
        while pagination_token:
            if rv.status_code != 200:
                raise Exception(rv.text)

            response_json = rv.json()

            pagination_token = response_json.get('nextPageToken')
            media_items = response_json['mediaItems']

            for media_item in media_items:
                yield GooglePhotosImage(media_item)

            if pagination_token:
                rv = GooglePhotosAPI._get_images_from_album(api_token, album, pagination_token)
