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

import uuid
from collections import namedtuple
from typing import Optional

import click
import requests

DEFAULT_SERVER = 'http://localhost:5000'
SESSION_SERVER = 'https://sessionserver.mojang.com/session/minecraft'

Identity = namedtuple("Identity", ["name", "user_id", "access_token"])


class SkinServerError(Exception):
    pass


def error_response(f):
    def decorator(*args, **kwargs):
        resp: requests.Response = f(*args, **kwargs)
        try:
            resp.raise_for_status()
            return resp
        except requests.HTTPError:
            error = resp.json()
            resp.close()
            raise click.ClickException(f"{error}")

    return decorator


class SkinServer:
    def __init__(self, host):
        self.host = host
        self.session = requests.Session()
        self.identity: Optional[Identity] = None

        self.session.request = error_response(self.session.request)

    def login(self, identity: Identity):
        self.identity = identity
        name, user_id, access_token = identity
        with self.session.post(f"{self.host}/auth/handshake", data={'name': name}) as r:
            r.raise_for_status()
            j = r.json()

        server_id = j['serverId']
        verify_token = j['verifyToken']

        with self.session.post(f'{SESSION_SERVER}/join', json={
            'accessToken': access_token,
            'selectedProfile': str(user_id).replace('-', ''),
            'serverId': server_id
        }) as r:
            r.raise_for_status()

        with self.session.post(f"{self.host}/auth/response", data={
            'name': name,
            'verifyToken': verify_token
        }) as r:
            r.raise_for_status()
            j = r.json()

        self.session.headers['Authorization'] = j['accessToken']

    def get(self, user: uuid.UUID):
        with self.session.get(f"{self.host}/api/v1/user/{user}") as r:
            r.raise_for_status()
            return r.json()

    def put_file(self, file, skin_type, **metadata):
        with self.session.put(f"{self.host}/api/v1/user/{self.identity.user_id}/{skin_type}", data=metadata,
                              files={'file': file}) as r:
            r.raise_for_status()

    def post_url(self, url, skin_type, **metadata):
        with self.session.post(f"{self.host}/api/v1/user/{self.identity.user_id}/{skin_type}",
                               data={'file': url, **metadata}) as r:
            r.raise_for_status()

    def delete(self, skin_type):
        with self.session.delete(f"{self.host}/api/v1/user/{self.identity.user_id}/{skin_type}") as r:
            r.raise_for_status()
            pass


@click.group()
@click.option("--host", default=DEFAULT_SERVER, show_default=True)
@click.pass_context
def cli(ctx, host):
    """Client for interacting with the skin server."""
    ctx.obj = SkinServer(host)


@cli.group("edit")
@click.option("--name", show_envvar=True, required=True)
@click.option("--user-id", type=uuid.UUID, show_envvar=True, required=True)
@click.password_option("--access-token", confirmation_prompt=False, show_envvar=True, required=True)
@click.pass_obj
def edit(server: SkinServer, name: str, user_id: uuid, access_token: str):
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
