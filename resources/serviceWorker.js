self.addEventListener('install', event => {
    console.log('installing service worker')
    event.waitUntil(
        caches.open('static').then(cache => {
            return cache.addAll([])
        }).then(() => {
            return self.skipWaiting()
        })
    )
})

self.addEventListener('activate', event => {
    console.log('service worker activated')
    return self.clients.claim()
})

//self.addEventListener('fetch', event => {
//    console.log('fetching ' + event.request.url)
//    event.respondWith(
//        caches.open('static').then(cache => {
//            return cache.match(event.request).then(response => {
//                console.log('matched ' + event.request.url)
//                let local = response
//                let remote = fetch(event.request).then(response => {
//                    console.log('fetched response from server ' + event.request.url)
//                    cache.put(event.request, response.clone())
//                    return response
//                })
//                return local || remote
//            })
//        })
//    );
//});
