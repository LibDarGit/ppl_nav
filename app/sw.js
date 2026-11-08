// PPL Nav service worker: app works offline; viewed map tiles are cached for use in flight.
const SHELL = 'pplnav-shell-__BUILD__';
const TILES = 'pplnav-tiles-v1';
const SHELL_FILES = ['./', './index.html', './manifest.webmanifest', './icon-192.png', './icon-512.png', './sql-wasm.js', './sql-wasm.wasm'];
const MAX_TILES = 4000;

self.addEventListener('install', e => {
  e.waitUntil(caches.open(SHELL).then(c => c.addAll(SHELL_FILES)));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys =>
    Promise.all(keys.filter(k => k !== SHELL && k !== TILES).map(k => caches.delete(k)))
  ).then(() => self.clients.claim()));
});

const isTile = url => /tile\.openstreetmap\.org|tile\.opentopomap\.org/.test(url.hostname);

async function trimTiles() {
  const c = await caches.open(TILES);
  const keys = await c.keys();
  if (keys.length > MAX_TILES) {
    for (const k of keys.slice(0, keys.length - MAX_TILES)) await c.delete(k);
  }
}

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET') return;

  if (isTile(url)) {
    // cache-first: tiles seen before the flight are available offline
    e.respondWith(caches.open(TILES).then(async c => {
      const hit = await c.match(e.request);
      if (hit) return hit;
      try {
        const res = await fetch(e.request);
        if (res.ok || res.type === 'opaque') { c.put(e.request, res.clone()); if (Math.random() < 0.05) trimTiles(); }
        return res;
      } catch (err) { return new Response('', { status: 504 }); }
    }));
    return;
  }

  if (url.origin === self.location.origin) {
    // stale-while-revalidate for the app itself
    e.respondWith(caches.open(SHELL).then(async c => {
      const hit = await c.match(e.request, { ignoreSearch: true });
      const net = fetch(e.request).then(res => { if (res.ok) c.put(e.request, res.clone()); return res; }).catch(() => null);
      return hit || (await net) || c.match('./index.html');
    }));
  }
});
