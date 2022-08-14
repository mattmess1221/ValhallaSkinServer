from ..models import Upload
from ..schemas import Texture


def test_texture_validation():
    texture = Texture.parse_obj({"meta": {}, "upload": Upload(hash="abc123")})
    assert texture.url == "https://localhost/textures/abc123"
