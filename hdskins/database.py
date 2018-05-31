#!/usr/env python3

import functools
import sqlite3
import time

from.import mojang


def singleton(class_):
    instances = {}

    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]
    return getinstance


@singleton
class Database(object):
    """An instance of a sql database"""

    def __init__(self, connection):
        self.connection = connection

    def setup(self):
        with self:
            self.cursor.executescript("""CREATE TABLE IF NOT EXISTS Users (
                ID          INT         PRIMARY KEY AUTOINCREMENT,
                ProfileId   CHAR(32)    NOT NULL UNIQUE,
                ProfileName CHAR(16)    NOT NULL
            );
            CREATE TABLE IF NOT EXISTS Textures (
                ID          INT         PRIMARY KEY AUTOINCREMENT,
                UserId      INT         NOT NULL,
                TextureType TEXT        NOT NULL,
                TextureURL  TEXT        NOT NULL,
                UploaderIP  TEXT        NOT NULL,
                UploadTime  TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP
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
        self.connection.close()

    def find_user(self, uuid, put=True):
        self.execute("SELECT * FROM Users WHERE ProfileId=?", (uuid))
        row = self.cursor.fetchone()
        if row is not None:
            return User(self, self.cursor.fetchone())
        if put:
            name = mojang.get_name(uuid)
            return self._put_user(uuid, name)
        return None

    def _get_user(self, id):
        self.execute("SELECT * FROM Users WHERE ID=?", (id))
        return User(self, self.cursor.fetchone())

    def _put_user(self, uuid, name):
        self.execute("INSERT INTO Users VALUES (?, ?)", (uuid, name))

    def _get_textures(self, userId, time=time.time):
        """Gets a dict of textures from the database if it exists"""
        self.execute("SELECT * FROM Users WHERE UserId = ?", (userId,))
        textures = []
        for row in self.cursor:
            textures.append(Texture(self, row))

        # Filter so the date is only 1

        return textures

    def _put_texture(self, userId, textureUrl, textureType, uploaderIP):
        self.execute("""INSERT INTO Textures VALUES (
            UserId ?,
            TextureURL ?,
            TextureType ?,
            UploaderIP ?
            ) """, (userId, textureUrl, textureType, uploaderIP))

        return Texture(self, self.cursor.fetchone())

    def _get_metadata(self, textureId):
        """Gets all metadata for this texture"""
        self.cursor.execute("SELECT * FROM Metadata WHERE TextureID = ?",
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


class Metadata(Row):

    @property
    def user(self): return self._row['UserId']

    @property
    def texture(self): return self._row['TextureId']

    @property
    def key(self): return self._row['Key']

    @property
    def val(self): return self._row['Value']
