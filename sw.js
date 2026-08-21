/* 영어로 문장 만들기 훈련 — 오프라인 캐시
   앱은 단일 HTML이라 셸 하나만 캐시하면 비행기 모드에서도 그대로 동작합니다.
   CACHE 값을 바꾸면 이전 캐시를 지우고 새로 받습니다. */
const CACHE = "esmt-2026-08-21c";
const SHELL = [
  "./",
  "./index.html",
  "./manifest.json",
  "./icon-192.png",
  "./icon-512.png",
  "./icon-maskable.png"
];

self.addEventListener("install", e => {
  // addAll 은 하나라도 실패하면 설치 전체가 무산된다 -> 개별로 담고 실패는 무시
  e.waitUntil(
    caches.open(CACHE)
      .then(c => Promise.all(SHELL.map(u => c.add(u).catch(() => {}))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  // API 호출(AI 첨삭)은 절대 캐시하지 않는다
  if (new URL(req.url).origin !== self.location.origin) return;

  // 네트워크 우선, 실패하면 캐시 (새 버전을 놓치지 않으면서 오프라인도 동작)
  e.respondWith(
    fetch(req)
      .then(res => {
        const copy = res.clone();
        caches.open(CACHE).then(c => c.put(req, copy)).catch(() => {});
        return res;
      })
      .catch(() => caches.match(req).then(hit => hit || caches.match("./index.html")))
  );
});
