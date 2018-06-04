#!/usr/env python3

import functools
import sqlite3
import time

from .mojang import fetch_profile_name


class Database(object):
    """An instance of a sql database"""

    def __init__(self, connection):
        self.connection = sqlite3.connect(connection)

    def setup(self):
        self.cursor.executescript("""CREATE TABLE IF NOT EXISTS HDSkins (
            Version     INT         NOT NULL
        );
        CREATE TABLE IF NOT EXISTS Users (
            ID          INTEGER     PRIMARY KEY AUTOINCREMENT,
            ProfileId   CHAR(32)    NOT NULL UNIQUE,
            ProfileName CHAR(16)    NOT NULL,
            Fetched     TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS Textures (
            ID          INTEGER     PRIMARY KEY AUTOINCREMENT,
            UserId      INTEGER     NOT NULL,
            TextureType TEXT        NOT NULL,
            TextureURL  TEXT        NOT NULL,
            UploaderIP  TEXT        NOT NULL,
            UploadTime  TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS EnabledSkins (
            ID          INTEGER     PRIMARY KEY AUTOINCREMENT,
            UserId      INTEGER     NOT NULL,
            TextureId   INTEGER     NOT NULL
        );
        CREATE TABLE IF NOT EXISTS Metadata (
            ID          INTEGER     PRIMARY KEY AUTOINCREMENT,
            TextureID   INTEGER     NOT NULL,
            'Key'       TEXT        NOT NULL,
            'Value'     TEXT
        );""")
        self.connection.commit()

    def __enter__(self):
        self.cursor = self.connection.cursor()
        return self

    def __exit__(self, type, value, traceback):
        self.connection.commit()
        self.connection.close()

    def find_user(self, uuid, put=True):
        self.cursor.execute(
            "SELECT * FROM Users WHERE ProfileId=?", (str(uuid),))
        row = self.cursor.fetchone()
        if row:
            user = User(self, row)

            month = 60 * 60 * 24 * 30
            fetched = int(user.time_fetched)
            # FIXME: update user. This logic is probably wrong
            if time.time() - fetched > month:
                new_name = fetch_profile_name(uuid)
                self.cursor.execute("""UPDATE Users WHERE ID=?
                       SET ProfileName = ?, Fetched = CURRENT_TIMESTAMP)""",
                                    (user._id, new_name))

            return user
        if put:
            name = fetch_profile_name(uuid)
            return self._put_user(uuid, name)
        return None

    def _get_user(self, id):
        self.cursor.execute("SELECT * FROM Users WHERE ID=?", (id,))
        return User(self, self.cursor.fetchone())

    def _put_user(self, uuid, name):
        self.cursor.execute("""INSERT INTO Users (ProfileId, ProfileName)
            VALUES(?, ?)""", (uuid, name))
        return self._get_user(self.cursor.lastrowid)

    def _get_textures(self, userId):
        """Gets a dict of textures from the database if it exists"""
        self.cursor.execute(
            "SELECT TextureId FROM EnabledSkins WHERE UserId = ?",
            (userId,))

        for (t_id,) in self.cursor:
            t = self._get_texture(t_id)
            print(type(t))
            yield t.type, t

    def _get_texture(self, textureId):
        self.cursor.execute(
            "SELECT * FROM Textures WHERE ID = ?", (textureId,))

        return Texture(self, self.cursor.fetchone())

    def _put_texture(self, userId, textureUrl, textureType, uploaderIP):
        self.cursor.execute("""INSERT INTO Textures
            (UserId, TextureURL, TextureType, UploaderIP)
            VALUES(?, ?, ?, ?)""",
                            (userId, textureUrl, textureType, uploaderIP))

        texture = self._get_texture(self.cursor.lastrowid)

        # TODO: learn sql. This is bad because of concurrent connections
        self.cursor.execute(
            "SELECT TextureId FROM EnabledSkins WHERE UserId=?", (userId,))
        for row in self.cursor:
            tex = self._get_texture(row[0])
            if tex.type == textureType:
                self.cursor.execute(
                    "DELETE FROM EnabledSkins WHERE UserId=? and TextureId=?",
                    (userId, tex._id))
                break

        self.cursor.execute(
            "INSERT INTO EnabledSkins (UserId, TextureId) VALUES (?, ?)",
            (userId, texture._id))

        return texture

    def _clear_texture(self, user, texture):
        self.cursor.execute(
            "DELETE FROM EnabledSkins WHERE UserId=? AND TextureId=?",
            (user, texture))
        return bool(self.cursor.rowcount & 1)

    def _get_metadata(self, textureId):
        """Gets all metadata for this texture"""
        self.cursor.execute(
            "SELECT * FROM Metadata WHERE TextureID=?", (textureId,))

        for row in self.cursor:
            yield Metadata(self, row)

    def _put_metadata(self, textureId, **kwargs):
        for k, v in kwargs.items():
            if k and v:
                self.cursor.execute("""INSERT INTO Metadata
                    (TextureId, 'Key', 'Value')
                    VALUES (?, ?, ?)""", (textureId, k, v))
        return self._get_metadata(textureId)


class Row(object):

    ID = 0

    def __init__(self, db, row):
        self._db = db
        self._row = row

    @property
    def _id(self):
        return self._row[self.ID]


class User(Row):

    NAME = 1
    UUID = 2
    FETCHED = 3

    @property
    def name(self): return self._row[self.NAME]

    @property
    def uniqueId(self): return self._row[self.UUID]

    @property
    def time_fetched(self):
        date = self._row[self.FETCHED]
        self._db.cursor.execute("SELECT strftime('%s', ?)", (date,))
        return self._db.cursor.fetchone()[0]

    @property
    def textures(self): return self._db._get_textures(self._id)

    def put_texture(self, url, skinType, uploader):
        return self._db._put_texture(self._id, url, skinType, uploader)


class Texture(Row):

    USER = 1
    TYPE = 2
    URL = 3
    TIME = 4
    UPLODER = 5

    @property
    def _user(self): return self._row[self.USER]

    @property
    def type(self): return self._row[self.TYPE]

    @property
    def url(self): return self._row[self.URL]

    @property
    def timestamp(self): return self._row[self.TIME]

    @property
    def uploader(self): return self._row[self.UPLODER]

    @property
    def metadata(self): return self._db._get_metadata(self._id)

    def put_metadata(self, **kwargs):
        return self._db._put_metadata(self._id, **kwargs)

    def clear(self):
        """Clears this texture from enabled skins.

        :returns bool: Whether this texture was enabled.
        """
        return self._db._clear_texture(self._user, self._id)


class Metadata(Row):

    TEX = 1
    KEY = 2
    VAL = 3

    @property
    def _texture(self): return self._row[self.TEX]

    @property
    def key(self): return self._row[self.KEY]

    @property
    def val(self): return self._row[self.VAL]
