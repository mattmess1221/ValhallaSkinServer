#!/usr/env python3

import functools
import sqlite3
import time

from .mojang import fetch_profile_name


class Database(object):
    """An instance of a sql database"""

    def __init__(self, connection):
        self.connection = connection

    def setup(self):
        with self:
            self.cursor.executescript("""CREATE TABLE IF NOT EXISTS HDSkins (
                Version     INT         NOT NULL
            );
            CREATE TABLE IF NOT EXISTS Users (
                ID          INT         PRIMARY KEY AUTOINCREMENT,
                ProfileId   CHAR(32)    NOT NULL UNIQUE,
                ProfileName CHAR(16)    NOT NULL,
                Fetched     TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS Textures (
                ID          INT         PRIMARY KEY AUTOINCREMENT,
                UserId      INT         NOT NULL,
                TextureType TEXT        NOT NULL,
                TextureURL  TEXT        NOT NULL,
                UploaderIP  TEXT        NOT NULL,
                UploadTime  TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS EnabledSkins (
                ID          INT         PRIMARY KEY AUTOINCREMENT,
                UserId      INT         NOT NULL,
                TextureId   INT         NOT NULL
            );
            CREATE TABLE IF NOT EXISTS Metadata (
                ID          INT         PRIMARY KEY AUTOINCREMENT,
                UserId      INT         NOT NULL
                TextureID   INT         NOT NULL,
                'Key'       TEXT        NOT NULL,
                'Value'     TEXT
            );""")

    def __enter__(self):
        self.cursor = self.connection.cursor()
        return self

    def __exit__(self, type, value, traceback):
        self.connection.commit()
        self.connection.close()

    def find_user(self, uuid, put=True):
        self.execute("SELECT * FROM Users WHERE ProfileId=?", (uuid))
        row = self.cursor.fetchone()
        if row:
            user = User(self, self.cursor.fetchone())

            month = 60 * 60 * 24 * 30
            # FIXME: update user. This logic is probably wrong
            if time.time - user.time_fetched > month:
                new_name = fetch_profile_name(uuid)
                self.execute("""UPDATE Users WHERE ID=? VALUES
                       (ProfileName ?, Fetched CURRENT_TIMESTAMP) """,
                             (user._id, new_name))

            return user
        if put:
            name = fetch_profile_name(uuid)
            return self._put_user(uuid, name)
        return None

    def _get_user(self, id):
        self.execute("SELECT * FROM Users WHERE ID=?", (id))
        return User(self, self.cursor.fetchone())

    def _put_user(self, uuid, name):
        self.execute("INSERT INTO Users VALUES (?, ?)", (uuid, name))

    def _get_textures(self, userId):
        """Gets a dict of textures from the database if it exists"""
        self.execute(
            "SELECT TextureId FROM EnabledSkins WHERE UserId = ?",
            (userId,))

        for (t_id,) in self.cursor:
            t = self._get_texture(t_id)
            yield t.type, t

    def _get_texture(self, textureId):
        self.execute(
            "SELECT * FROM Textures WHERE TextureId = ?", (textureId,))

        return Texture(self, self.cursor.fetchone())

    def _put_texture(self, userId, textureUrl, textureType, uploaderIP):
        self.execute("""INSERT INTO Textures VALUES (
            UserId ?,
            TextureURL ?,
            TextureType ?,
            UploaderIP ?
            ) """, (userId, textureUrl, textureType, uploaderIP))

        texture = Texture(self, self.cursor.fetchone())

        # TODO: learn sql. This is bad because of concurrent connections
        self.execute(
            "SELECT TextureId FROM EnabledSkins WHERE UserId=?", (userId,))
        for row in self.cursor:
            tex = self._get_texture(row['TextureId'])
            if tex.type is textureType:
                self.execute(
                    "DELETE FROM EnabledSkins WHERE UserId=? and TextureId=?",
                    (userId, tex._id))
                break

        self.execute(
            "INSERT INTO EnabledSkins VALUES (?, ?)",
            (userId, texture._id))

        return texture

    def _clear_texture(self, user, texture):
        self.execute(
            "DELETE FROM EnabledSkins WHERE UserId=? AND TextureId=?",
            (user, texture))
        return bool(self.cursor.rowcount & 1)

    def _get_metadata(self, textureId):
        """Gets all metadata for this texture"""
        self.cursor.execute("SELECT * FROM Metadata WHERE TextureID=?",
                            textureId)
        metadata = []
        for row in self.cursor:
            metadata.append(Metadata(self, row))
        return metadata

    def _put_metadata(self, textureId, key, value):
        self.execute("""INSERT INTO Metadata VALUES (
            TextureId ?,
            'Key' ?,
            'Value' ?
            """, (textureId, key, value))
        return Metadata(self, self.cursor.fetchone())

    def execute(self, sql, args=()):
        self.cursor.execute(sql, args)


class Row(object):

    def __init__(self, db, row):
        self._db = db
        self._row = row

    @property
    def _id(self): return self._row['ID']


class User(Row):

    @property
    def name(self): return self._row['ProfileName']

    @property
    def uniqueId(self): return self._row['ProfileId']

    @property
    def time_fetched(self): return self._row['Fetched']

    @property
    def textures(self): return self._db._get_textures(self._id)

    def put_texture(self, url, skinType, uploader):
        return self._db._put_texture(self._id, url, skinType, uploader)


class Texture(Row):

    @property
    def user(self): return self._row['UserId']

    @property
    def type(self): return self._row['TextureType']

    @property
    def url(self): return self._row['TextureURL']

    @property
    def timestamp(self): return self._row['UploadTime']

    @property
    def uploader(self): return self._row['UploaderIP']

    @property
    def metadata(self): return self._db._get_metadata(self._id)

    def put_metadata(self, key, val):
        return self._db._put_metadata(self._id, key, val)

    def clear(self):
        """Clears this texture from enabled skins.

        :returns bool: Whether this texture was enabled.
        """
        return self._db._clear_texture(self.user, self._id)


class Metadata(Row):

    @property
    def user(self): return self._row['UserId']

    @property
    def texture(self): return self._row['TextureId']

    @property
    def key(self): return self._row['Key']

    @property
    def val(self): return self._row['Value']
