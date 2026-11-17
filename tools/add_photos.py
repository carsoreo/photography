"""Adds photos to the gallery: a 2400px web copy and a 900px thumbnail, both without metadata, plus a
photos.js entry whose camera details are read from the original before they are stripped.

Run from the repo root:  python tools/add_photos.py picks.json
picks.json is a list of {"file": original, "collection": one of the four, "shop": Redbubble work id or "",
"place": caption place or ""}. A pick whose shop id is already in photos.js is skipped, so it is safe to rerun.
Needs Pillow only.
"""
import io, json, os, sys
from datetime import datetime
from PIL import Image, ImageCms, ImageOps

HEAD = "// Generated from the Darktable exports. Metadata already stripped from the images.\nwindow.PHOTOS = "
CAMERAS = {"Canon EOS REBEL SL1": "Canon Rebel SL1", "E-500": "Olympus E-500"}  # EXIF name -> name on the site

js = io.open("photos.js", encoding="utf-8").read()
photos = json.loads(js[js.index("["):js.rindex("]") + 1])
linked = {p["shop"] for p in photos if p.get("shop")}

for pick in json.load(io.open(sys.argv[1], encoding="utf-8")):
    if pick["shop"] and pick["shop"] in linked:
        continue
    kind = pick["collection"]
    n = sum(p["collection"] == kind for p in photos) + 1
    src, thumb = f"photos/{kind}/{kind}-{n:02d}.jpg", f"photos/{kind}/{kind}-{n:02d}-sm.jpg"
    assert not os.path.exists(src), src

    im = Image.open(pick["file"])
    exif = im.getexif()
    shot = exif.get_ifd(0x8769)  # the camera-settings block
    assert shot[0x829A] < 1, f"{pick['file']}: exposures of a second or longer need a new settings format"
    settings = f"{round(shot[0x920A])}mm · f/{float(shot[0x829D]):g} · 1/{round(1 / shot[0x829A])}s · ISO {shot[0x8827]}"
    model = exif[0x0110].strip()
    # Read everything from the original before any file is written, so a photo that fails leaves nothing behind.
    # The Olympus leaves the "taken" date empty; its file date is the next best.
    date = datetime.strptime(shot.get(0x9003) or exif[0x0132], "%Y:%m:%d %H:%M:%S").strftime("%b %Y")

    # Dropping the colour profile is only safe once the pixels are sRGB.
    icc = im.info.get("icc_profile")
    im = ImageOps.exif_transpose(im).convert("RGB")
    if icc:
        im = ImageCms.profileToProfile(im, ImageCms.ImageCmsProfile(io.BytesIO(icc)), ImageCms.createProfile("sRGB"))
    im.thumbnail((2400, 2400), Image.LANCZOS)  # never enlarges
    im.save(src, quality=84, progressive=True, optimize=True)  # a fresh save writes no metadata
    im.thumbnail((900, 900), Image.LANCZOS)
    im.save(thumb, quality=80, progressive=True, optimize=True)

    entry = {
        "src": src, "shop": pick["shop"], "thumb": thumb, "collection": kind, "w": im.width, "h": im.height,
        "place": pick["place"], "date": date,
        "camera": CAMERAS.get(model, model), "lens": shot.get(0xA434, ""), "settings": settings,
    }
    if not entry["shop"]:
        del entry["shop"]
    # After the last photo of its collection, so the viewer pages through photos in the order the grid shows them.
    last = max(i for i, p in enumerate(photos) if p["collection"] == kind)
    photos.insert(last + 1, entry)
    print(src, im.size, entry["date"], entry["camera"], settings)

io.open("photos.js", "w", encoding="utf-8", newline="\n").write(HEAD + json.dumps(photos, indent=1) + ";\n")
print(len(photos), "photos")
