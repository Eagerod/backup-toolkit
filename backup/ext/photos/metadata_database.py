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
                metadata text,
                touched datetime
            );
        """)

        cls.cursor().execute("""
            CREATE TABLE IF NOT EXISTS deleted_images (
                id text,
                md5 text,
                filename text,
                metadata text,
                deleted datetime
            );
        """)

        cls.cursor().execute("""
            CREATE TABLE IF NOT EXISTS albums (
                id text,
                title text,
                metadata text
            );
        """)

        cls.cursor().execute("""
            CREATE TABLE IF NOT EXISTS album_images (
                album text,
                image text
            );
        """)

        cls.db().commit()

    @classmethod
    def has_metadata(cls, media_item):
        return cls.cursor().execute('SELECT id FROM images WHERE id = ?', (media_item.id,)).fetchone() is not None

    @classmethod
    def touch_metadata(cls, media_item, touch_datetime):
        cursor = cls.cursor().execute('UPDATE images set touched = ? where id = ?', (touch_datetime, media_item.id))
        cls.db().commit()
        return cursor.rowcount == 1

    @classmethod
    def has_album(cls, album):
        return cls.cursor().execute('SELECT id FROM albums WHERE id = ?', (album.id,)).fetchone() is not None

    @classmethod
    def has_album_image(cls, album, media_item):
        return cls.cursor().execute("""
            SELECT * FROM album_images WHERE album = ? AND image = ?
        """, (album.id, media_item.id)).fetchone() is not None

    @classmethod
    def add_image(cls, media_item, md5, touch_datetime):
        cls.cursor().execute("""
            INSERT INTO images VALUES (?, ?, ?, ?, ?)
        """, (media_item.id, md5, media_item.filename, json.dumps(media_item.json), touch_datetime)
        )
        cls.db().commit()

    @classmethod
    def add_album(cls, album):
        cls.cursor().execute("""
            INSERT INTO albums VALUES (?, ?, ?)
        """, (album.id, album.title, json.dumps(album.json))
        )
        cls.db().commit()

    @classmethod
    def items_in_album(cls, album):
        res = cls.cursor().execute("""
            SELECT COUNT(*) FROM album_images WHERE album = ?
        """, (album.id,)).fetchone()
        return res[0] if res else 0

    @classmethod
    def add_album_image(cls, album, media_item):
        cls.cursor().execute("""
            INSERT INTO album_images VALUES (?, ?)
        """, (album.id, media_item.id))
        cls.db().commit()

    @classmethod
    def images_with_prefix(cls, prefix):
        return (row[0] for row in cls.cursor().execute("""
            SELECT id FROM images WHERE id like ?
        """, ('{}%'.format(prefix),)).fetchall())

    @classmethod
    def deleted_image_ids(cls, touch_datetime):
        cursor = cls.db().cursor().execute("""
            SELECT id FROM images WHERE touched != ?
        """, (touch_datetime,))

        for r in cursor:
            yield r[0]

    @classmethod
    def delete_metadata(cls, image_id):
        cls.cursor().execute("""
            INSERT INTO deleted_images
                SELECT id, md5, filename, metadata, DATETIME() FROM images WHERE id = ?
        """, (image_id,))
        cls.cursor().execute("""
            DELETE FROM images WHERE id = ?
        """, (image_id,))
        cls.db().commit()
