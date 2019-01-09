import throttle from 'lodash.throttle'

function dragElement(element) {
    let xDiff = 0,
        yDiff = 0,
        xStart = 0,
        yStart = 0

    element.onmousedown = startDragging

    function startDragging(e) {
        if (e.button !== 0) return
        xStart = e.clientX
        yStart = e.clientY
        document.onmouseup = endDragging
        document.onmousemove = onDragging
        e.preventDefault()
        e.stopPropagation()
    }

    const onDragging = throttle(e => {
        xDiff = xStart - e.clientX
        yDiff = yStart - e.clientY
        xStart = e.clientX
        yStart = e.clientY
        element.style.top = `${(element.offsetTop - yDiff)}px`
        element.style.left = `${(element.offsetLeft - xDiff)}px`
        e.preventDefault()
        e.stopPropagation()
    }, 16)

    function endDragging(e) {
        document.onmouseup = null
        document.onmousemove = null
        e.preventDefault()
        e.stopPropagation()
    }
}

/**
 * Generate border radius for the given corners.
 * For instance, 1000 means the top left corner is round.
 * @param {number} roundCorner a four digit number indicating which cornors are round.
 */
function roundCorners(corners) {
    const c = i => corners.charAt(i) === '1' ? 'var(--small-radius)' : '0'
    return `border-radius: ${c(0)} ${c(1)} ${c(2)} ${c(3)};`
}

export {
    dragElement,
    roundCorners,
}
