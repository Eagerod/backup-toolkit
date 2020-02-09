import json
import hashlib
import os
import sys
from datetime import datetime

import google.auth.transport.requests
import google.oauth2
from core.extensions import BackupExtension

from .google_photos_api import GooglePhotosAPI, GoogleCredentialsProvider
from .metadata_database import MetadataDatabase


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SECRETS_FILE_PATH = os.path.join(ROOT_DIR, 'credentials.json')
METADATA_DATABASE_FILENAME = 'metadata.sqlite3'
DELETED_IMAGES_PATH = 'deleted'

# Use the first 8 characters of the item id as a directory for each file
IMAGE_DIRECTORY_PREFIX_LENGTH = 8
GOOGLE_PHOTOS_READ_ONLY_SCOPES = [
    'photoslibrary.readonly'
]
AUTH_TOKEN_ENV_NAME = 'GOOGLE_PHOTOS_REFRESH_TOKEN'


class PhotosBackupCliOptions(object):
    AUTHENTICATE = 'authenticate'
    RUN = 'run'


class Extension(BackupExtension):
    PHOTOS_BACKUP_SUBCOMMAND_NAME = 'photos'

    def __init__(self, *args, **kwargs):
        super(Extension, self).__init__(*args, **kwargs)

        self.parser.add_argument(
            '--credentials_file',
            '-c',
            help='path to a Google service/app credentials file',
            required=True
        )

        self.subparsers = self.parser.add_subparsers(dest='photos_command', help='photos sub-commands')

        run_parser = self.subparsers.add_parser(PhotosBackupCliOptions.RUN)
        self.subparsers.add_parser(PhotosBackupCliOptions.AUTHENTICATE)

        run_parser.add_argument(
            '--metadata_db',
            '-m',
            help='path to metadata db file (default ${output_dir}/metadata.db)'
        )
        run_parser.add_argument('output_dir', nargs=1, help='path to output backup files to')

    @classmethod
    def get_extension_name(cls):
        return cls.PHOTOS_BACKUP_SUBCOMMAND_NAME

    def run(self, args):
        if args.photos_command == PhotosBackupCliOptions.RUN:
            self.do_backup(args)
        elif args.photos_command == PhotosBackupCliOptions.AUTHENTICATE:
            self.do_authenticate(args)
        else:
            self.parser.print_usage(sys.stderr)
            sys.exit(2)

    def do_authenticate(self, args):
        if os.environ.get(AUTH_TOKEN_ENV_NAME):
            print('\x1b[31mGoogle Photos API token found.\x1b[0m', file=sys.stderr)
            print('\x1b[31mOnly proceed if you intend to replace the existing auth token.\x1b[0m', file=sys.stderr)

        token = GoogleCredentialsProvider.get_access_token(args.credentials_file, GOOGLE_PHOTOS_READ_ONLY_SCOPES)
        print('Use this token to authenticate other {} photos commands'.format(sys.argv[0]), file=sys.stderr)
        print(token)

    def refresh_local_album_metadata(self, g_auth):
        for album in GooglePhotosAPI.enumerate_albums(g_auth):
            if not MetadataDatabase.has_album(album):
                MetadataDatabase.add_album(album)

            print('Updating local metadata for album {}'.format(album.title), file=sys.stderr)
            if int(MetadataDatabase.items_in_album(album)) != int(album.media_items_count):
                # Top up the database with whatever is missing.
                for media_item in GooglePhotosAPI.enumerate_images_in_album(g_auth, album):
                    if MetadataDatabase.has_album_image(album, media_item):
                        continue

                    MetadataDatabase.add_album_image(album, media_item)

    def handle_image_stream(self, fh, hash_alg):
        def handle_image_stream_closure(b):
            fh.write(b)
            hash_alg.update(b)
        return handle_image_stream_closure

    def download_images(self, g_auth, output_dir, touch_datetime):
        for media_item in GooglePhotosAPI.enumerate_images(g_auth):
            if MetadataDatabase.touch_metadata(media_item, touch_datetime):
                continue

            print('New photo ({})'.format(media_item.filename), file=sys.stderr)

            directory = media_item.id[0:IMAGE_DIRECTORY_PREFIX_LENGTH]
            filename = media_item.id[IMAGE_DIRECTORY_PREFIX_LENGTH:]
            full_dir = os.path.join(output_dir, directory)

            if not os.path.exists(full_dir):
                os.mkdir(full_dir)

            filepath = os.path.join(full_dir, filename)
            md5_alg = hashlib.md5()

            # Because media items can be hundreds of MB (for videos), stream
            #   everything to keep memory consumption low.
            with open(filepath, 'wb') as f:
                bytes_fn = self.handle_image_stream(f, md5_alg)
                GooglePhotosAPI.stream_media_item_content(g_auth, media_item, bytes_fn)

            md5 = md5_alg.hexdigest()

            MetadataDatabase.add_image(media_item, md5, touch_datetime)

    def delete_image(self, output_dir, image_id):
        deleted_images_dir = os.path.join(output_dir, DELETED_IMAGES_PATH)
        directory = image_id[0:IMAGE_DIRECTORY_PREFIX_LENGTH]
        filename = image_id[IMAGE_DIRECTORY_PREFIX_LENGTH:]

        source_path = os.path.join(output_dir, directory, filename)
        dest_path = os.path.join(deleted_images_dir, image_id)

        if not os.path.exists(source_path):
            print('    It appears as though the photo has already been deleted. Only clearing metadata.')
            MetadataDatabase.delete_metadata(image_id)
            return

        if not os.path.exists(deleted_images_dir):
            os.mkdir(deleted_images_dir)

        os.rename(source_path, dest_path)

        MetadataDatabase.delete_metadata(image_id)

    def delete_images(self, output_dir, touch_datetime):
        for deleted_image in MetadataDatabase.deleted_image_ids(touch_datetime):
            print('Deleting image {} because it was removed from Google Photos.'.format(deleted_image))
            self.delete_image(output_dir, deleted_image)

    def move_orphans(self, output_dir):
        # For each prefix, verify that the right files are present in the
        #   metadata database.
        # For any folder that doesn't have the right number of files, move all
        #   undesirable files to the deleted directory.
        for dirname in os.listdir(output_dir):
            if dirname == DELETED_IMAGES_PATH:
                continue

            dirpath = os.path.join(output_dir, dirname)
            if not os.path.isdir(dirpath):
                continue

            filenames = os.listdir(dirpath)
            sqlite_safe_dirname = dirname.replace('_', '\\_')
            for image_id in MetadataDatabase.images_with_prefix(sqlite_safe_dirname):
                fn = image_id[IMAGE_DIRECTORY_PREFIX_LENGTH:]
                if fn not in filenames:
                    print('Deleting image {} because it has no metadata.'.format(image_id))
                    self.delete_image(output_dir, image_id)

    def do_backup(self, args):
        if not os.environ.get(AUTH_TOKEN_ENV_NAME):
            print('Google Photos API token not found. Run:', file=sys.stderr)
            print(' {} photos authenticate'.format(sys.argv[0]), file=sys.stderr)
            print('To get a token and export it in {}'.format(AUTH_TOKEN_ENV_NAME), file=sys.stderr)
            sys.exit(3)

        output_dir = args.output_dir[0]
        auth = os.environ[AUTH_TOKEN_ENV_NAME]

        # Refresh
        with open(args.credentials_file) as f:
            credentials = json.load(f)['installed']

        creds = google.oauth2.credentials.Credentials(
            '',
            refresh_token=auth,
            token_uri=credentials['token_uri'],
            client_id=credentials['client_id'],
            client_secret=credentials['client_secret']
        )

        creds.refresh(google.auth.transport.requests.Request())
        print('Refreshed auth token for this session', file=sys.stderr)
        auth = creds.token

        if not os.path.exists(output_dir):
            os.mkdir(output_dir)

        if args.metadata_db:
            metadata_db_path = args.metadata_db
        else:
            metadata_db_path = os.path.join(output_dir, METADATA_DATABASE_FILENAME)

        MetadataDatabase.init(metadata_db_path)
        MetadataDatabase.create()

        # Build up list local albums
        print('Updating local albums...', file=sys.stderr)
        self.refresh_local_album_metadata(auth)

        touch_datetime = datetime.utcnow()
        print('Downloading images...', file=sys.stderr)
        self.download_images(auth, output_dir, touch_datetime)

        print('Removing deleted photos...')
        self.delete_images(output_dir, touch_datetime)

        print('Cleaning up orphaned files...')
        self.move_orphans(output_dir)


__all__ = ['Extension']
