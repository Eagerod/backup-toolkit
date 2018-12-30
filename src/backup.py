import argparse
import hashlib
import json
import os
import sqlite3

import requests

from google_photos_api import GoogleCredentialsProvider, GooglePhotosAPI


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SECRETS_FILE_PATH = os.path.join(ROOT_DIR, 'credentials.json')
METADATA_DATABASE_FILENAME = 'metadata.sqlite3'

GOOGLE_PHOTOS_READ_ONLY_SCOPES = [
    'photoslibrary.readonly'
]


class MetadataDatabase(object):
    """
    Note -- This class is not something that's meant to be used in any kind of
      production environment. It was entirely built for writing pretty, and not
      necessarily very functional, or error-handled entrypoint code.
    """
    __db_path__ = None
    __db__ = None
    __cursor__ = None

    @classmethod
    def db(cls):
        if cls.__db__:
            return cls.__db__

        cls.__db__ = sqlite3.connect(cls.__db_path__)
        return cls.__db__

    @classmethod
    def cursor(cls):
        if cls.__cursor__:
            return cls.__cursor__

        cls.__cursor__ = cls.db().cursor()
        return cls.__cursor__

    @classmethod
    def init(cls, database_path):
        cls.__db_path__ = database_path

    @classmethod
    def create(cls):
        cls.cursor().execute("""
            CREATE TABLE IF NOT EXISTS images (
                id text,
                md5 text,
                filename text,
                metadata text
            );
        """)
        cls.db().commit()

    @classmethod
    def has_metadata(cls, media_item):
        return cls.cursor().execute('SELECT id FROM images where id = ?', (media_item['id'],)).fetchone() is not None

    @classmethod
    def add_item(cls, media_item, md5):
        cls.cursor().execute("""
            INSERT INTO images VALUES (?, ?, ?, ?)
        """, (media_item['id'], md5, media_item['filename'], json.dumps(media_item))
        )
        cls.db().commit()


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
            media_item['baseUrl'],
            media_item['mediaMetadata']['width'],
            media_item['mediaMetadata']['height']
        )

        media_item_content = requests.get(dl_url).content
        md5 = hashlib.md5(media_item_content).hexdigest()

        # Use the first 8 characters of the item id as a directory for each
        #   file that's written.
        directory = media_item['id'][0:8]
        full_dir = os.path.join(output_dir, directory)

        if not os.path.exists(full_dir):
            os.mkdir(full_dir)

        filepath = os.path.join(full_dir, media_item['filename'])
        with open(filepath, 'w') as f:
            f.write(media_item_content)

        MetadataDatabase.add_item(media_item, md5)


if __name__ == '__main__':
    do_program()
