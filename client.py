#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Client for interacting with the skin server.

It's suggested to save some options as environment variables. e.g.

$ export HDSKINS_EDIT_USER_ID="<minecraft uuid>"
$ export HDSKINS_EDIT_NAME="<minecraft name>"
$ export HDSKINS_EDIT_ACCESS_TOKEN="<minecraft access token>"

All this info can be grabbed from your launcher_profiles.json file in your .minecraft folder.

Note: This script requires python3.7, requests, and click.

Examples:

# Upload a skin from a url
$ ./client.py edit url <some url>

# Upload an elytra from a local file
$ ./client.py edit file <some file> --type elytra

# Delete the skin
$ ./client.py edit delete

# Get all the textures for a user
$ ./client.py show <some user id>

"""

import logging
import sys
import uuid
from collections import namedtuple
from typing import Optional, Type

import click
import requests

DEFAULT_SERVER = 'http://localhost:5000'
SESSION_SERVER = 'https://sessionserver.mojang.com/session/minecraft'

Identity = namedtuple("Identity", ["name", "user_id", "access_token"])


class MojangError(Exception):
    pass


class HDSkinsError(Exception):
    pass


def verify_error(response: requests.Response, wrap_exc: Type[Exception] = HDSkinsError):
    try:
        response.raise_for_status()
    except requests.HTTPError:
        raise wrap_exc(response.text)


class SkinServer:
    def __init__(self, host):
        self.host = host
        self.session = requests.Session()
        self.identity: Optional[Identity] = None

    def login(self, identity: Identity):
        self.identity = identity
        name, user_id, access_token = identity

        logging.info("Logging in...")
        logging.info("Skin Server = %s", self.host)
        logging.info("Login name = %s", name)
        logging.info("Login uuid = %s", user_id)

        url = f"{self.host}/auth/handshake"

        logging.debug(f"Sending auth handshake to {url}")
        with self.session.post(url, data={'name': name}) as r:
            verify_error(r)
            j = r.json()

        logging.debug(f"Auth handshake response = {j}")

        server_id = j['serverId']
        verify_token = j['verifyToken']

        logging.debug("Authenticating with Mojang")

        with self.session.post(f'{SESSION_SERVER}/join', json={
            'accessToken': access_token,
            'selectedProfile': str(user_id).replace('-', ''),
            'serverId': server_id
        }) as r:
            verify_error(r, MojangError)

        url = f"{self.host}/auth/response"

        logging.debug(f"Sending auth response to {url}")
        with self.session.post(url, data={'name': name, 'verifyToken': verify_token}) as r:
            verify_error(r)
            j = r.json()

        self.session.headers['Authorization'] = j['accessToken']

        logging.info("Login complete")

    def get(self, user: uuid.UUID):
        logging.info("Getting textures owned by %s", user)
        with self.session.get(f"{self.host}/api/v1/user/{user}") as r:
            verify_error(r)
            return r.json()

    def put_file(self, file, skin_type, **metadata):
        logging.info("Uploading %s for %s", skin_type, self.identity.name)
        with self.session.put(f"{self.host}/api/v1/user/{self.identity.user_id}/{skin_type}", data=metadata,
                              files={'file': file}) as r:
            verify_error(r)

        logging.info("Done")

    def post_url(self, url, skin_type, **metadata):
        logging.info("Uploading %s for %s", skin_type, self.identity.name)
        with self.session.post(f"{self.host}/api/v1/user/{self.identity.user_id}/{skin_type}",
                               data={'file': url, **metadata}) as r:
            verify_error(r)

        logging.info("Done")

    def delete(self, skin_type):
        logging.info("Deleting %s for %s", skin_type, self.identity.name)
        with self.session.delete(f"{self.host}/api/v1/user/{self.identity.user_id}/{skin_type}") as r:
            verify_error(r)

        logging.info("Done")


@click.group()
@click.option("--host", default=DEFAULT_SERVER, show_default=True, show_envvar=True)
@click.option("-v", count=True)
@click.pass_context
def cli(ctx, host, v):
    """Client for interacting with the skin server."""
    ctx.obj = SkinServer(host)

    logging.basicConfig(level=logging.getLevelName(logging.WARNING - (v * 10)))

    @ctx.call_on_close
    def on_close():
        exc_type, exc_value, exc_tb = sys.exc_info()
        if isinstance(exc_value, (MojangError, HDSkinsError)):
            raise click.ClickException(f"{exc_type.__name__}: {exc_value}")


# Allows passing root arguments from sub-commands. e.g. edit file $filename -vv --host=$skin_host
cli.allow_interspersed_args = True


@cli.group("edit")
@click.option("--name", show_envvar=True, required=True)
@click.option("--user-id", type=uuid.UUID, show_envvar=True, required=True)
@click.password_option("--access-token", confirmation_prompt=False, show_envvar=True, required=True)
@click.pass_obj
def edit(server: SkinServer, name: str, user_id: uuid.UUID, access_token: str):
    """Sub-command to edit your textures on the server"""
    server.login(Identity(name, user_id, access_token))


@edit.command("file")
@click.argument("file", type=click.File('rb'))
@click.option("--type", default="skin")
@click.pass_obj
def put_file(server: SkinServer, file, type):
    """Uploads a texture from your local machine"""
    server.put_file(file, type)


@edit.command("url")
@click.argument("url")
@click.option("--type", default="skin")
@click.pass_obj
def post_url(server: SkinServer, url, type):
    """Uploads a texture from the internet."""
    server.post_url(url, type)


@edit.command("delete")
@click.option("--type", default="skin")
@click.pass_obj
def delete_skin(server: SkinServer, type):
    """Deletes the current texture from the server"""
    server.delete(type)


@cli.command("show")
@click.argument("user-id", type=uuid.UUID)
@click.pass_obj
def show(server: SkinServer, user_id):
    """Show a user's texture data"""
    click.echo(server.get(user_id)['textures'])


if __name__ == '__main__':
    cli(auto_envvar_prefix="HDSKINS")
