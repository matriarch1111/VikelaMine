self.addEventListener('install', e=>{
  e.waitUntil(caches.open('vikela-v2').then(c=>c.addAll(['/','/report-hazard/'])));
});
self.addEventListener('activate', e=>{
  e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(key=>key.startsWith('vikela-')&&key!=='vikela-v2').map(key=>caches.delete(key)))));
});
self.addEventListener('fetch', e=>{
  e.respondWith(fetch(e.request).catch(()=>caches.match(e.request)));
});