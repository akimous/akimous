//const log = console.log
const log = () => {}

self.addEventListener('install', event => {
    console.log('installing service worker')
    event.waitUntil(
        caches.open('static').then(cache => {
            return cache.addAll(['/'])
        }).then(() => {
            return self.skipWaiting()
        })
    )
})

self.addEventListener('activate', event => {
    log('service worker activated', event)
    return self.clients.claim()
})

self.addEventListener('fetch', event => {
    log('fetching ' + event.request.url)
    event.respondWith((() => {
        if (event.request.method !== 'GET')
            return fetch(event.request)

        else return caches.open('static').then(cache => {
            return cache.match(event.request).then(response => {
                log('matched ' + event.request.url)
                let local = response
                let remote = fetch(event.request).then(response => {
                    cache.put(event.request, response.clone())
                    log('updated cache ' + event.request.url)
                    return response
                }).catch(error => {
                    console.error(`failed to fetch request ${event.request.url}`, error)
                })
                return remote || local
            })
        })
    })())
})
