from uuid import UUID

from sqlalchemy.exc import NoResultFound
from werkzeug.routing import BaseConverter

from .models import User


class UserConverter(BaseConverter):
    def to_python(self, value):
        try:
            uuid = UUID(value)
            return User.query.filter_by(uuid=uuid).one()
        except (ValueError, NoResultFound):
            return None

    def to_url(self, value):
        if isinstance(value, User):
            uuid = value.uuid
        else:
            uuid = value
        return str(uuid)
