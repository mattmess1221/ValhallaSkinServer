from uuid import UUID

import click
from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as _Session

from .. import models


def migrate(query, title):
    total = query.count()
    for i, t in enumerate(query):
        click.echo(f"\rMigrating {title} {i}/{total}", nl=False)
        yield t
    click.echo()


def fix_index(table, value):
    models.db.engine.execute(F"ALTER SEQUENCE {table.__tablename__}_id_seq RESTART WITH {value};")


def init_app(app: Flask):
    from . import old_models
    Session = sessionmaker()

    @app.cli.command("reset-secret")
    def reset_secret():
        models.SecretSanity.query.delete()
        models.db.session.commit()

    @app.cli.command("migrate-data")
    @click.argument("old_db")
    def migrate_data(old_db):
        """Migrates data from the old database format to the newer one."""
        old_engine = create_engine(old_db)
        old_session: _Session = Session(bind=old_engine)

        max_id = 0
        u: old_models.Uploader
        for u in migrate(old_session.query(old_models.User), "Users"):
            max_id = max(max_id, u.id)
            models.db.session.add(models.User(
                id=u.id,
                uuid=UUID(u.uuid),
                name=u.name,
                address="0.0.0.0"
            ))
        fix_index(models.User, max_id + 1)

        max_id = 0
        upload: old_models.Upload
        for upload in migrate(old_session.query(old_models.Upload), "Uploads"):
            max_id = max(max_id, upload.id)
            models.db.session.add(models.Upload(
                id=upload.id,
                hash=upload.hash,
                user_id=upload.uploader_obj.user,
                upload_time=upload.upload_time
            ))
        fix_index(models.Upload, max_id + 1)

        max_id = 0
        tex: old_models.Texture
        for tex in migrate(old_session.query(old_models.Texture), "Textures"):
            max_id = max(max_id, tex.id)
            meta = {
                m.key: m.value
                for m in (old_session.query(old_models.Metadata).get(i) for i in tex.metadata_.split('|')[1:-1])
            } if tex.metadata_ else {}
            models.db.session.add(models.Texture(
                id=tex.id,
                user_id=tex.user,
                upload_id=tex.file,
                tex_type=tex.tex_type,
                meta=meta
            ))
        fix_index(models.Texture, max_id + 1)

        click.echo("Committing...")
        models.db.session.commit()
