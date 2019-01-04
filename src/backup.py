import argparse
import hashlib
import os

import requests

from google_photos_api import GoogleCredentialsProvider, GooglePhotosAPI
from metadata_database import MetadataDatabase


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SECRETS_FILE_PATH = os.path.join(ROOT_DIR, 'credentials.json')
METADATA_DATABASE_FILENAME = 'metadata.sqlite3'

GOOGLE_PHOTOS_READ_ONLY_SCOPES = [
    'photoslibrary.readonly'
]


def do_program():
    parser = argparse.ArgumentParser(description='Bare bones Google Photos local downloader')

    parser.add_argument('--credentials-file', '-c', help='path to a google service/app credentials file.')
    parser.add_argument('output_dir', nargs=1, help='path to output backup files to')

    args = parser.parse_args()

    output_dir = args.output_dir[0]

    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    metadata_db_path = os.path.join(output_dir, METADATA_DATABASE_FILENAME)
    MetadataDatabase.init(metadata_db_path)
    MetadataDatabase.create()

    secrets_file = args.credentials_file if args.credentials_file else SECRETS_FILE_PATH
    auth = GoogleCredentialsProvider.get_access_token(secrets_file, GOOGLE_PHOTOS_READ_ONLY_SCOPES)

    for media_item in GooglePhotosAPI.enumerate_images(auth):
        if MetadataDatabase.has_metadata(media_item):
            continue

        # Google asks for us to provide the width and height parameter, and to
        #   retain image metadata, include the `-d` parameter.
        dl_url = '{}=w{}-h{}-d'.format(
            media_item.base_url,
            media_item.media_metadata['width'],
            media_item.media_metadata['height']
        )

        media_item_content = requests.get(dl_url).content
        md5 = hashlib.md5(media_item_content).hexdigest()

        # Use the first 8 characters of the item id as a directory for each
        #   file that's written.
        directory = media_item.id[0:8]
        filename = media_item.id[8:]
        full_dir = os.path.join(output_dir, directory)

        if not os.path.exists(full_dir):
            os.mkdir(full_dir)

        filepath = os.path.join(full_dir, filename)
        with open(filepath, 'w') as f:
            f.write(media_item_content)

        MetadataDatabase.add_item(media_item, md5)


if __name__ == '__main__':
    do_program()
