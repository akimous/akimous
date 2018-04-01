// https://stackoverflow.com/questions/22697936/binary-search-in-javascript
function binarySearch(array, target) {
    let lo = -1,
        hi = array.length
    while (1 + lo !== hi) {
        const mi = lo + ((hi - lo) >> 1)
        if (array[mi].name >= target) hi = mi
        else lo = mi
    }
    return hi
}

function onIdle(callback, timeout = 7000, delay = 1) {
    setTimeout(() => { // let other things run first
        if (window.requestIdleCallback) {
            window.requestIdleCallback(() => {
                requestAnimationFrame(callback)
            }, {
                timeout
            })
        } else {
            requestAnimationFrame(() => {
                console.warn('requestIdleCallback not available')
                requestAnimationFrame(callback)
            })
        }
    }, delay)
}

function initializeTabView(view, title, icon) {
    view.set({
        self: view,
    })
    view.children = {}
    setTimeout(() => {
        view.parent = view.get('parent')
        view.tab = view.parent.tabBar.openTab(view, title, icon)
        view.observe('active', active => {
            view.tab.set({
                active
            })
        })
    })
}

function setAttributeForMultipleComponent(obj, ...targets) {
    for (const i of targets)
        i.set(obj)
}

export {
    binarySearch,
    onIdle,
    initializeTabView,
    setAttributeForMultipleComponent
}
