from ..schemas import Texture


def test_texture_validation():
    url = "http://localhost/textures/abc123"
    texture = Texture.parse_obj({"meta": {}, "url": url})
    assert texture.url == url
