import hashlib
import os

import requests
from core.extensions import BackupExtension

from google_photos_api import GooglePhotosAPI, GoogleCredentialsProvider
from metadata_database import MetadataDatabase


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SECRETS_FILE_PATH = os.path.join(ROOT_DIR, 'credentials.json')
METADATA_DATABASE_FILENAME = 'metadata.sqlite3'

# Use the first 8 characters of the item id as a directory for each file
IMAGE_DIRECTORY_PREFIX_LENGTH = 8
GOOGLE_PHOTOS_READ_ONLY_SCOPES = [
    'photoslibrary.readonly'
]


class Extension(BackupExtension):
    PHOTOS_BACKUP_SUBCOMMAND_NAME = 'photos'

    def __init__(self, *args, **kwargs):
        super(Extension, self).__init__(*args, **kwargs)

        self.parser.add_argument('--credentials-file', '-c', help='path to a google service/app credentials file.')
        self.parser.add_argument('output_dir', nargs=1, help='path to output backup files to')

    @classmethod
    def get_extension_name(cls):
        return cls.PHOTOS_BACKUP_SUBCOMMAND_NAME

    def run(self, args):
        output_dir = args.output_dir[0]

        if not os.path.exists(output_dir):
            os.mkdir(output_dir)

        metadata_db_path = os.path.join(output_dir, METADATA_DATABASE_FILENAME)
        MetadataDatabase.init(metadata_db_path)
        MetadataDatabase.create()

        secrets_file = args.credentials_file if args.credentials_file else SECRETS_FILE_PATH
        auth = GoogleCredentialsProvider.get_access_token(secrets_file, GOOGLE_PHOTOS_READ_ONLY_SCOPES)

        # Build up list local albums
        for album in GooglePhotosAPI.enumerate_albums(auth):
            if not MetadataDatabase.has_album(album):
                MetadataDatabase.add_album(album)

            if int(MetadataDatabase.items_in_album(album)) != int(album.media_items_count):
                # Top up the database with whatever is missing.
                for media_item in GooglePhotosAPI.enumerate_images_in_album(auth, album):
                    if MetadataDatabase.has_album_image(album, media_item):
                        continue

                    MetadataDatabase.add_album_image(album, media_item)

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

            directory = media_item.id[0:IMAGE_DIRECTORY_PREFIX_LENGTH]
            filename = media_item.id[IMAGE_DIRECTORY_PREFIX_LENGTH:]
            full_dir = os.path.join(output_dir, directory)

            if not os.path.exists(full_dir):
                os.mkdir(full_dir)

            filepath = os.path.join(full_dir, filename)
            with open(filepath, 'w') as f:
                f.write(media_item_content)

            MetadataDatabase.add_image(media_item, md5)


__all__ = ['Extension']