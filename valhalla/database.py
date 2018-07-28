#!/usr/env python3

import datetime
import functools
from datetime import datetime, timedelta

from pydal import DAL, Field, SQLCustomType

from .mojang import fetch_profile_name


class Database():
    """An instance of a sql database"""

    def __init__(self, path):

        self.db = db = DAL(path, lazy_tables=True)

        db.define_table(
            'users',
            Field('uuid', 'string', length='32', notnull=True, unique=True),
            Field('name', 'string', length='16', notnull=True),
            Field('fetched', 'datetime', default=datetime.now))

        db.define_table(
            'uploaders',
            Field('user', 'reference users', notnull=True),
            Field('address', 'string', notnull=True),
            Field('accessed', 'datetime', default=datetime.now, notnull=True))

        db.define_table(
            'uploads',
            Field('hash', 'string', notnull=True, unique=True),
            Field('uploader', 'reference uploaders', notnull=True),
            Field('upload_time', 'datetime', default=datetime.now, notnull=True))

        db.define_table(
            'textures',
            Field('user', 'reference users', notnull=True),
            Field('tex_type', 'string', notnull=True),
            Field('file', 'reference uploads'),
            Field('metadata', 'list:reference metadata'))

        db.define_table(
            'metadata',
            Field('key', 'string', notnull=True),
            Field('value', 'string'))

        db.define_table(
            'tokens',
            Field('uploader', 'reference uploaders',
                  notnull=True, unique=True),
            Field('token', 'string', notnull=True),
            Field('issued', 'datetime', default=datetime.now, notnull=True))

        db.commit()

    def commit(self):
        self.db.commit()

    def find_user(self, uuid, name=None):
        if name is not None:
            self.db.users.update_or_insert(
                self.db.users.uuid == uuid, uuid=uuid, name=name)
            self.commit()
        user = self.db(self.db.users.uuid == uuid).select().first()
        if user is None:
            return None

        month = timedelta(days=30)
        fetched = user.fetched

        # Refetch names after a month.
        # TODO: Have this scheduled in batches
        # if name is None or datetime.now() - fetched > month:
        #     user.name = fetch_profile_name(user.uuid)
        #     user.fetched = datetime.now()

        return user

    def find_textures(self, user):
        return self.db(self.db.textures.user == user).select()\
            .sort(lambda row: row.file.upload_time)\
            .group_by_value('tex_type', one_result=True)

    def find_uploader(self, user, addr):
        self.db.uploaders.update_or_insert(user=user, address=addr)
        self.db.commit()
        return self.db((self.db.uploaders.user == user) & (self.db.uploaders.address == addr)).select().first()

    def find_token(self, uploader):
        return self.db(self.db.tokens.uploader == uploader).select().first()

    def put_token(self, uploader, token):
        self.db.tokens.update_or_insert(self.db.tokens.uploader == uploader,
                                        uploader=uploader,
                                        token=token,
                                        issued=datetime.now())

    def clear_token(self, uploader):
        self.db(self.db.tokens.uploader == uploader).delete()
