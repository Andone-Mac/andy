/* 机悟JAVIS App（PWA）service worker：
 * 保守缓存策略——页面/动态内容一律网络优先（官网每晚 18:06 更新行业动态，必须实时），
 * 静态资源（css/js/图片/图标）缓存优先；视频(mp4)与大媒体直接透传不占本地配额。
 * 取不到网络时（离线）回退到最近一次缓存的同 URL，再兜底到首页。*/
var CACHE = 'jiwu-javis-v1';

self.addEventListener('install', function (e) { self.skipWaiting(); });

self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.filter(function (k) { return k !== CACHE; }).map(function (k) { return caches.delete(k); }));
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener('fetch', function (e) {
  var req = e.request;
  if (req.method !== 'GET') return;
  var u = new URL(req.url);
  if (u.origin !== self.location.origin) return;
  if (u.pathname.indexOf('/api') === 0) return;              // 线索接口永不缓存
  if (u.pathname.indexOf('/videos/') !== 0 && /\.(mp4|m4v|webm)$/i.test(u.pathname)) return; // 大媒体透传

  var isStatic = /\.(css|js|png|jpg|jpeg|svg|ico|webp|woff2?|manifest)$/i.test(u.pathname) || u.pathname === '/manifest.json';
  if (isStatic) {
    e.respondWith(
      caches.open(CACHE).then(function (c) {
        return c.match(req).then(function (hit) {
          if (hit) return hit;
          return fetch(req).then(function (res) {
            if (res && res.ok) c.put(req, res.clone());
            return res;
          });
        });
      })
    );
    return;
  }
  // 页面：网络优先，失败回退缓存
  e.respondWith(
    fetch(req).then(function (res) {
      if (res && res.ok && u.pathname !== '/sw.js') {
        var cl = res.clone();
        caches.open(CACHE).then(function (c) { c.put(req, cl); });
      }
      return res;
    }).catch(function () {
      return caches.match(req).then(function (hit) { return hit || caches.match('/index.html'); });
    })
  );
});
