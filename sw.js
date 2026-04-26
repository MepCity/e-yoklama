const CACHE_NAME = 'e-yoklama-v1';
const CORE_ASSETS = [
  '/',
  '/login',
  '/static/css/style.css',
  '/static/js/app.js',
  '/static/js/offline.js'
];

self.addEventListener('install', function (event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function (cache) {
      return cache.addAll(CORE_ASSETS);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.map(function (key) {
        if (key !== CACHE_NAME) {
          return caches.delete(key);
        }
        return null;
      }));
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', function (event) {
  const request = event.request;

  if (request.method !== 'GET') {
    return;
  }

  event.respondWith(
    fetch(request).then(function (response) {
      const copy = response.clone();
      caches.open(CACHE_NAME).then(function (cache) {
        cache.put(request, copy);
      });
      return response;
    }).catch(function () {
      return caches.match(request).then(function (cached) {
        return cached || caches.match('/login');
      });
    })
  );
});
