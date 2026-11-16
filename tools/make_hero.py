"""Splits the hero photo into two layers so the eagle can fly in on page load:

  hero-sky.jpg     the sky with the eagle painted out
  hero-eagle.webp  the eagle alone on a transparent background, same frame as the sky

Run from the repo root:  python tools/make_hero.py
Needs Pillow only. Neither output carries metadata (Pillow writes none unless asked).
"""
from PIL import Image, ImageChops, ImageFilter, ImageMath

SRC = "photos/wildlife/wildlife-30.jpg"
img = Image.open(SRC).convert("RGB")


def distance(a, b):
    """Largest per-channel difference between two images, as one greyscale image."""
    r, g, b_ = ImageChops.difference(a, b).split()
    return ImageChops.lighter(ImageChops.lighter(r, g), b_)


# 1. Rough mask: anything far from a heavily blurred copy is bird, then grown so it covers the soft edges.
rough = distance(img, img.filter(ImageFilter.GaussianBlur(120))).point(lambda v: 255 if v > 30 else 0)
rough = rough.filter(ImageFilter.MedianFilter(5)).filter(ImageFilter.MaxFilter(41))

# 2. Sky under the bird, worked out at 1/8 size (there is no detail there to lose). Each pass fills the rim of
#    the hole from the known sky around it (blurred colour / blurred coverage), then counts that rim as known,
#    until the hole is closed. One big blur instead would divide by almost nothing in the middle of the hole.
small = img.reduce(8)
hole = rough.reduce(8).point(lambda v: 255 if v else 0)
while hole.getbbox():
    known = ImageChops.invert(hole)
    weight = known.filter(ImageFilter.GaussianBlur(6))
    held = Image.composite(small, Image.new("RGB", small.size), known).filter(ImageFilter.GaussianBlur(6))
    guess = Image.merge("RGB", [
        ImageMath.lambda_eval(lambda _: _["c"] * 255.0 / _["max"](_["w"], 1), c=band, w=weight).convert("L")
        for band in held.split()
    ])
    rim = ImageChops.multiply(hole, weight.point(lambda v: 255 if v >= 48 else 0))
    small = Image.composite(guess, small, rim)
    hole = ImageChops.subtract(hole, rim)
fill = small.resize(img.size, Image.BICUBIC)

# 3. Give the fill the photo's own grain, borrowed from clear sky to the right, or the patch would look airbrushed.
donor = ImageChops.offset(img, -600, 0)
grain = ImageChops.subtract(donor, donor.filter(ImageFilter.GaussianBlur(4)), scale=1, offset=128)
fill = ImageChops.add(fill, grain, scale=1, offset=-128)
sky = Image.composite(fill, img, rough.filter(ImageFilter.GaussianBlur(8)))

# 4. Matte: how far each pixel is from the bird-free sky, ramped from clear (grain level) to solid.
LOW, HIGH = 16, 44
alpha = distance(img, sky).point(lambda v: max(0, min(255, (v - LOW) * 255 // (HIGH - LOW))))
alpha = ImageChops.multiply(alpha.filter(ImageFilter.MedianFilter(3)), rough)
eagle = img.copy()
eagle.putalpha(alpha)

sky.save("hero-sky.jpg", quality=86, progressive=True, optimize=True)
eagle.save("hero-eagle.webp", quality=90, method=6)
print("bird box:", alpha.getbbox(), "of", img.size)
