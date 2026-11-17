# photography

[![tests](https://github.com/carsoreo/photography/actions/workflows/test.yml/badge.svg)](https://github.com/carsoreo/photography/actions/workflows/test.yml)
[![Live gallery](https://img.shields.io/badge/live-carsoreo.github.io%2Fphotography-007190?style=flat-square)](https://carsoreo.github.io/photography/)
[![Instagram](https://img.shields.io/badge/@car__sore-0D2B33?style=flat-square&logo=instagram&logoColor=96D1AA)](https://www.instagram.com/car_sore/)
![Photos](https://img.shields.io/badge/photos-115-00978D?style=flat-square)

Wildlife, landscape and street photography by Carson Orejola. It's a dark, gallery-style static site with no framework.

**→ [carsoreo.github.io/photography](https://carsoreo.github.io/photography/)**

## Features

- **The eagle flies in.** On load the bald eagle glides into the hero from the right and my name follows it. The bird is its own transparent layer, cut out of the photo by [`tools/make_hero.py`](tools/make_hero.py), over the same sky with the bird painted out.
- **Four collections:** wildlife (mostly birds), landscapes, street and details.
- **Full-screen viewer** with keyboard (← → Esc) and swipe navigation, showing where and when each shot was taken plus the camera, lens and exposure. The photo grows out of its thumbnail and shrinks back into it (a view transition), and the thumbnail stands in until the full-size file arrives.
- **Every photo has its own link.** While a photo is open its name is in the address (`#wildlife-30`), and that address opens the same photo.
- **EXIF explorer:** four linked charts of focal length, aperture, shutter speed and ISO across every photo. Pointing at a bar shows that slice in the other three; selecting it lists the photos.
- **Fast loading:** small thumbnails in the grid, full-size images only in the viewer, lazy-loaded and decoded off the main thread.
- **Privacy by default:** images are resized and stripped of metadata (including GPS) before they're committed. Captions come from a separate data file, so only the details I choose are published.

## How it works

```
Darktable export ──▶ resize + strip metadata ──▶ photos/<collection>/*.jpg (+ -sm thumbnails)
                                └──────────────▶ photos.js  (caption + EXIF data)
index.html  reads window.PHOTOS from photos.js and renders the grid and viewer
```

To add photos, list the originals in a JSON file and run [`tools/add_photos.py`](tools/add_photos.py); it makes both sizes, strips the metadata and adds the entries to `photos.js`.

Each entry in `photos.js` looks like:

```js
{
  src: "photos/wildlife/wildlife-01.jpg",
  thumb: "photos/wildlife/wildlife-01-sm.jpg",
  collection: "wildlife",
  w: 900, h: 600,        // aspect ratio of the grid tile
  place: "Chattanooga, TN",
  date: "Aug 2026",
  camera: "Canon EOS R7",
  lens: "RF100-400mm F5.6-8 IS USM",
  settings: "400mm · f/8 · 1/500s · ISO 4000"
}
```

## Tests

```sh
node --test
```

The tests read `photos.js` and every image under `photos/`. They check that each listed photo and thumbnail exists, has the listed shape and contains no EXIF or XMP metadata, that no image is published without being listed, and that the photo count in this README is current. They run on every push.

## Gear

Canon EOS R7 with the RF 100-400mm, and the Canon Rebel SL1 for older work. Edited in Darktable.

## License

The code is free to reuse. The photographs are © Carson Orejola, all rights reserved. Please ask before using them.
