// Generates a 1024x1024 PNG icon for the calculator (no external deps).
// Uses Node's built-in zlib for PNG encoding. Run via: `node scripts/gen-icons.mjs`
import { writeFileSync, mkdirSync } from 'node:fs';
import { deflateSync, crc32 } from 'node:zlib';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT = resolve(__dirname, '..', 'src-tauri', 'icons');
mkdirSync(OUT, { recursive: true });

const W = 1024;
const H = 1024;

// Color helper: blend two colors smoothly across the canvas (simple linear gradient)
function colorAt(x, y) {
  // background: deep slate
  const bgTop = [11, 13, 18]; // #0b0d12
  const bgBot = [26, 29, 41]; // #1a1d29
  const t = y / (H - 1);
  const r = Math.round(bgTop[0] + (bgBot[0] - bgTop[0]) * t);
  const g = Math.round(bgTop[1] + (bgBot[1] - bgTop[1]) * t);
  const b = Math.round(bgTop[2] + (bgBot[2] - bgTop[2]) * t);
  return [r, g, b, 255];
}

// Draw a rounded-rect "app icon" body filled with bg gradient + orange equals bar + digits hint
function isInsideIcon(x, y) {
  const radius = 200;
  const left = 64, right = W - 64, top = 64, bot = H - 64;
  if (x < left || x > right || y < top || y > bot) return false;
  if (x < left + radius && y < top + radius) {
    const dx = left + radius - x, dy = top + radius - y;
    return dx * dx + dy * dy <= radius * radius;
  }
  if (x > right - radius && y < top + radius) {
    const dx = x - (right - radius), dy = top + radius - y;
    return dx * dx + dy * dy <= radius * radius;
  }
  if (x < left + radius && y > bot - radius) {
    const dx = left + radius - x, dy = y - (bot - radius);
    return dx * dx + dy * dy <= radius * radius;
  }
  if (x > right - radius && y > bot - radius) {
    const dx = x - (right - radius), dy = y - (bot - radius);
    return dx * dx + dy * dy <= radius * radius;
  }
  return true;
}

function pixel(x, y) {
  if (!isInsideIcon(x, y)) return [0, 0, 0, 0];
  const [r, g, b, a] = colorAt(x, y);
  // equals bar
  const eqTop = 720, eqBot = 760;
  if (y >= eqTop && y <= eqBot) {
    return [255, 159, 10, 255];
  }
  const eqTop2 = 660, eqBot2 = 700;
  if (y >= eqTop2 && y <= eqBot2) {
    return [255, 159, 10, 255];
  }
  // small digit dot near top
  if (x >= 500 && x <= 560 && y >= 280 && y <= 340) {
    return [245, 247, 251, 255];
  }
  return [r, g, b, a];
}

function buildRawRgba() {
  const rowSize = W * 4 + 1;
  const raw = Buffer.alloc(rowSize * H);
  for (let y = 0; y < H; y++) {
    const off = y * rowSize;
    raw[off] = 0; // filter byte: None
    for (let x = 0; x < W; x++) {
      const p = pixel(x, y);
      const i = off + 1 + x * 4;
      raw[i] = p[0];
      raw[i + 1] = p[1];
      raw[i + 2] = p[2];
      raw[i + 3] = p[3];
    }
  }
  return raw;
}

function chunk(type, data) {
  const len = Buffer.alloc(4);
  len.writeUInt32BE(data.length, 0);
  const typeBuf = Buffer.from(type, 'ascii');
  const crcBuf = Buffer.alloc(4);
  crcBuf.writeUInt32BE(crc32(Buffer.concat([typeBuf, data])) >>> 0, 0);
  return Buffer.concat([len, typeBuf, data, crcBuf]);
}

function encodePng(width, height, rgba) {
  const sig = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0);
  ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 8;     // bit depth
  ihdr[9] = 6;     // color type: RGBA
  ihdr[10] = 0;    // compression
  ihdr[11] = 0;    // filter
  ihdr[12] = 0;    // interlace
  const idat = deflateSync(rgba);
  return Buffer.concat([
    sig,
    chunk('IHDR', ihdr),
    chunk('IDAT', idat),
    chunk('IEND', Buffer.alloc(0)),
  ]);
}

const raw = buildRawRgba();
const png = encodePng(W, H, raw);
const out = resolve(OUT, 'source.png');
writeFileSync(out, png);
console.log('Wrote', out, '(' + png.length + ' bytes)');
