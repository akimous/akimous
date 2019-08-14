import throttle from 'lodash.throttle'
import { tick } from 'svelte'

import g from './Globals'
import { setProjectState } from './ConfigManager'

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
 * @param {number} roundCorner a four digit number indicating which corners are round.
 */
function roundCorners(corners) {
    const c = i => corners.charAt(i) === '1' ? 'var(--small-radius)' : '0'
    return `border-radius: ${c(0)} ${c(1)} ${c(2)} ${c(3)};`
}

async function makeScrollable(componentName, target) {
    await tick()
    const component = g[componentName]
    if (!component.keyEventHandler)
        component.keyEventHandler = {
            handleKeyEvent() {
                return true // not handled
            },
            handleCommand(command, target) {
                switch (command) {
                    case 'scrollUp':
                        target.scroll(-0.5)
                        break
                    case 'scrollDown':
                        target.scroll(0.5)
                        break
                    default:
                        return true // if not handled
                }
                return false
            }
        }

    let currentAnimationId, scrollUnit, t

    function step() {
        target.scrollTop += scrollUnit * t
        if (--t < 1) return
        currentAnimationId = requestAnimationFrame(step)
    }
    component.scroll = (amount) => {
        cancelAnimationFrame(currentAnimationId)
        const duration = 15 // frames
        const numberOfSteps = (duration + 1) * duration / 2
        scrollUnit = target.getBoundingClientRect().height * amount / numberOfSteps
        t = duration
        step()
    }
}

function onTabChangeFactory(tabBar, children, panel) {
    function onTabChange({ detail }) {
        if (detail.active) {
            for (const [name, view] of Object.entries(children)) {
                if (name !== detail.id && view) {
                    view.$set({ active: false })
                }
            }
            // no need to save panel middle, because it is already handled by ActivateEditor
            if (g.ready && panel) 
                setProjectState('activePanels', { [panel]: detail.id })
        }
        tabBar.updateTabIndicator(detail)
    }
    return onTabChange
}

export {
    dragElement,
    roundCorners,
    makeScrollable,
    onTabChangeFactory,
}
