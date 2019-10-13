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


def init_app(app: Flask):
    from . import old_models
    Session = sessionmaker()

    @app.cli.command("migrate-data")
    @click.argument("old_db")
    def main(old_db):
        """Migrates data from the old database format to the newer one."""
        old_engine = create_engine(old_db)
        old_session: _Session = Session(bind=old_engine)

        u: old_models.Uploader
        for u in migrate(old_session.query(old_models.User), "Users"):
            models.db.session.add(models.User(
                id=u.id,
                uuid=UUID(u.uuid),
                name=u.name,
                address="0.0.0.0"
            ))

        upload: old_models.Upload
        for upload in migrate(old_session.query(old_models.Upload), "Uploads"):
            models.db.session.add(models.Upload(
                id=upload.id,
                hash=upload.hash,
                user_id=upload.uploader_obj.user,
                upload_time=upload.upload_time
            ))

        tex: old_models.Texture
        for tex in migrate(old_session.query(old_models.Texture), "Textures"):
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

        click.echo("Committing...")
        models.db.session.commit()
