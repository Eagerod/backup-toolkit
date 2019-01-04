import json
import sqlite3


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

        cls.cursor().execute("""
            CREATE TABLE IF NOT EXISTS albums (
                id text,
                title text,
                metadata text
            );
        """)

        cls.db().commit()

    @classmethod
    def has_metadata(cls, media_item):
        return cls.cursor().execute('SELECT id FROM images where id = ?', (media_item.id,)).fetchone() is not None

    @classmethod
    def has_album(cls, album):
        return cls.cursor().execute('SELECT id FROM albums where id = ?', (album.id,)).fetchone() is not None

    @classmethod
    def add_image(cls, media_item, md5):
        cls.cursor().execute("""
            INSERT INTO images VALUES (?, ?, ?, ?)
        """, (media_item.id, md5, media_item.filename, json.dumps(media_item.json))
        )
        cls.db().commit()

    @classmethod
    def add_album(cls, album):
        cls.cursor().execute("""
            INSERT INTO albums VALUES (?, ?, ?)
        """, (album.id, album.title, json.dumps(album.json))
        )
        cls.db().commit()
