// Checks photos.js against the image files: every photo exists, has a thumbnail, matches its listed
// shape, and carries no EXIF/GPS metadata. Run with `node --test`.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const root = new URL('../', import.meta.url);
const read = (path) => fs.readFileSync(new URL(path, root));

const sandbox = { window: {} };
vm.runInNewContext(read('photos.js').toString(), sandbox);
const photos = sandbox.window.PHOTOS;

// Reads a JPEG's markers: its pixel size (from the SOF segment) and whether it has an EXIF or XMP block.
function jpegInfo(buf) {
  assert.ok(buf[0] === 0xff && buf[1] === 0xd8, 'not a JPEG');
  let i = 2, exif = false;
  while (i + 4 <= buf.length) {
    if (buf[i] !== 0xff) throw new Error(`bad marker at byte ${i}`);
    const marker = buf[i + 1];
    const len = buf.readUInt16BE(i + 2);
    if (marker === 0xe1) exif = true; // APP1 holds EXIF (camera, GPS) or XMP metadata
    // SOF0-SOF15, except DHT (C4), JPG (C8) and DAC (CC)
    if (marker >= 0xc0 && marker <= 0xcf && ![0xc4, 0xc8, 0xcc].includes(marker)) {
      return { h: buf.readUInt16BE(i + 5), w: buf.readUInt16BE(i + 7), exif };
    }
    i += 2 + len;
  }
  throw new Error('no SOF segment');
}

test('photos.js lists photos with the fields the gallery reads', () => {
  assert.ok(photos.length > 0);
  for (const p of photos) {
    for (const key of ['src', 'thumb', 'collection', 'date', 'camera', 'settings']) {
      assert.equal(typeof p[key], 'string', `${p.src}: ${key}`);
    }
    assert.ok(['wildlife', 'landscapes', 'street', 'details'].includes(p.collection), `${p.src}: collection ${p.collection}`);
    assert.ok(p.src.startsWith(`photos/${p.collection}/`), `${p.src} is outside its collection folder`);
    assert.ok(Number.isInteger(p.w) && Number.isInteger(p.h), `${p.src}: w/h`);
  }
});

// The EXIF charts in index.html parse these four values; a new shape (say a "2s" exposure) should fail here, not vanish from a chart.
test('every photo has the four camera settings the EXIF charts read', () => {
  for (const p of photos) assert.match(p.settings, /^\d+mm · f\/[\d.]+ · 1\/\d+s · ISO \d+$/, `${p.src}: ${p.settings}`);
});

test('no photo is listed twice', () => {
  const srcs = photos.map((p) => p.src);
  assert.equal(new Set(srcs).size, srcs.length);
});

test("every photo and thumbnail exists, has the listed shape and no EXIF", () => {
  for (const p of photos) {
    const full = jpegInfo(read(p.src));
    // w and h only set the grid tile's aspect ratio, so they must match the image's shape, not its pixels.
    assert.ok(Math.abs(full.w / full.h - p.w / p.h) < 0.01, `${p.src}: listed as ${p.w}x${p.h}, image is ${full.w}x${full.h}`);
    assert.equal(full.exif, false, `${p.src} still has EXIF or XMP metadata`);

    const thumb = jpegInfo(read(p.thumb));
    assert.equal(thumb.exif, false, `${p.thumb} still has EXIF or XMP metadata`);
    assert.ok(thumb.w < full.w, `${p.thumb} is not smaller than the full image`);
    // Same orientation and aspect ratio (within rounding), so the grid doesn't crop wrongly.
    assert.ok(Math.abs(thumb.w / thumb.h - full.w / full.h) < 0.02, `${p.thumb} has a different aspect ratio`);
  }
});

test('every image in photos/ is listed, so nothing is published by accident', () => {
  const listed = new Set(photos.flatMap((p) => [p.src, p.thumb]));
  for (const dir of fs.readdirSync(new URL('photos/', root))) {
    for (const file of fs.readdirSync(new URL(`photos/${dir}/`, root))) {
      assert.ok(listed.has(`photos/${dir}/${file}`), `photos/${dir}/${file} is not in photos.js`);
    }
  }
});

test('the hero layers match the eagle photo and carry no metadata', () => {
  const sky = jpegInfo(read('hero-sky.jpg')), photo = jpegInfo(read('photos/wildlife/wildlife-30.jpg'));
  assert.equal(sky.exif, false, 'hero-sky.jpg has EXIF or XMP metadata');
  assert.deepEqual([sky.w, sky.h], [photo.w, photo.h]);
  // WebP keeps metadata in chunks named EXIF and XMP; the eagle layer must have neither.
  const eagle = read('hero-eagle.webp').toString('latin1');
  assert.ok(eagle.startsWith('RIFF'), 'hero-eagle.webp is not a WebP file');
  assert.ok(!eagle.includes('EXIF') && !eagle.includes('XMP '), 'hero-eagle.webp has metadata');
});

test('the README photo count matches photos.js', () => {
  const badge = read('README.md').toString().match(/badge\/photos-(\d+)-/);
  assert.equal(Number(badge?.[1]), photos.length);
});
