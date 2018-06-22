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

    function onDragging(e) {
        requestAnimationFrame(() => {
            xDiff = xStart - e.clientX
            yDiff = yStart - e.clientY
            xStart = e.clientX
            yStart = e.clientY
            element.style.top = `${(element.offsetTop - yDiff)}px`
            element.style.left = `${(element.offsetLeft - xDiff)}px`
            e.preventDefault()
            e.stopPropagation()
        })
    }

    function endDragging(e) {
        document.onmouseup = null
        document.onmousemove = null
        e.preventDefault()
        e.stopPropagation()
    }
}

export {
    dragElement
}
