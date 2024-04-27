from pathlib import Path

assets = Path(__file__).parent

textures_url = "http://testserver/textures/"
steve_file = assets / "good/64x64.png"
steve_url = "http://assets.mojang.com/SkinTemplates/steve.png"
steve_hash = textures_url + steve_file.with_suffix(".txt").read_text().strip()

steve_file_data = (steve_file.name, steve_file.open("rb"), "image/png")
