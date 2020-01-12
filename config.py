"""Config objects used for valhalla

Required configurations via environment:

- SECRET_KEY

Required for production:

- SECRET_KEY        : Used to create and validate api tokens
- DATABASE_URL      : Connects to the database. uses format in RFC-1738
- TEXTURES_FS       : The filesystem URL to the textures location
- TEXTURES_DOMAIN   : The domain to point users to when requesting textures

"""

import os


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', "sqlite:///valhalla.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    TEXTURES_FS = os.getenv('TEXTURES_FS', './valhalla')
    OFFLINE = bool(os.getenv('OFFLINE', False))
    SKIN_BLACKLIST = ["cape"]

    CDN_DOMAIN = os.getenv("TEXTURES_DOMAIN")
    CDN_HTTPS = CDN_DOMAIN is not None
    CDN_ENDPOINTS = ["textures"]
    CDN_TIMESTAMP = False


class DebugConfig(Config):
    DEBUG = True
    ENV = "testing"
