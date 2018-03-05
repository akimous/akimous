import g from '../lib/Globals'

function EventDispatcherFactory(options) {
    const extraKeyHandler = options.extraKeyHandler
//    const dispatchTarget = options.dispatchTarget
    const closable = options.closable || true
//    if (!dispatchTarget) console.error('dispatchTarget is null')

    const handleKeyEvent = event => {
        const target = g.focus
//        const target = dispatchTarget.length > 1 ? g[dispatchTarget[0]][dispatchTarget[1]] : g[dispatchTarget[0]]
        if (!target) return true
        if (closable && !target.get('open')) return true

        switch (event.key) {
            case 'ArrowDown':
                target.move(1)
                break
            case 'ArrowUp':
                target.move(-1)
                break
            case 'Escape':
                closable && target.set({
                    open: false
                })
                break
            case ' ':
            case 'Enter':
                target.enter()
                break

            default:
                if (!extraKeyHandler) return true
                return extraKeyHandler(event, target)
        }
        event.preventDefault()
        event.stopPropagation()
        return false
    }

    const handleCommand = command => {
//        const target = dispatchTarget.length > 1 ? g[dispatchTarget[0]][dispatchTarget[1]] : g[dispatchTarget[0]]
        const target = g.focus
        if (closable && !target.get('open')) return false
        switch (command) {
            case 'down':
                target.move(1)
                return true
            case 'up':
                target.move(-1)
                return true
            case 'down5X':
                target.move(5)
                return true
            case 'up5X':
                target.move(-5)
                return true
            case 'bottom':
                target.move(999999)
                return true
            case 'top':
                target.move(-999999)
                return true
            case 'commit':
                target.enter()
                return true
            case '1':
            case '2':
            case '3':
            case '4':
            case '5':
            case '6':
            case '7':
            case '8':
                target.enter(+command)
                return true
        }
        console.error('unhandled command')
    }

    return {
        handleKeyEvent,
        handleCommand
    }
}

export default EventDispatcherFactory
