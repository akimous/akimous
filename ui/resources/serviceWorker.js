self.addEventListener('install', event => {
    event.waitUntil(
        caches.open('offline').then(cache => {
            return cache.addAll(['offline.html'])
        }).then(() => {
            return self.skipWaiting()
        })
    )
})

self.addEventListener('activate', event => {
    console.log('service worker activated')
    return self.clients.claim()
})

self.addEventListener('fetch', function (event) {
    const request = event.request
    if (request.method === 'GET') {
        event.respondWith(
            fetch(request).catch(function (error) {
                return caches.open('offline').then(function (cache) {
                    return cache.match('offline.html')
                })
            })
        )
    }
})
