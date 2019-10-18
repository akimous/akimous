//import g from '../lib/Globals'

function EventDispatcherFactory(options) {
    const extraKeyHandler = options.extraKeyHandler
    const target = options.target

    const handleKeyEvent = event => {
        let propagate = false
        switch (event.key) {
            case 'ArrowDown':
                target.move(1)
                break
            case 'ArrowUp':
                target.move(-1)
                break
            case 'Escape':
                target.closable && target.$set({ open: false })
                break
            case ' ':
            case 'Enter':
                propagate = target.enter(null, event.key)
                break
        }
        if (extraKeyHandler)
            return extraKeyHandler(event, target)
        return propagate
    }

    const handleCommand = command => {
        switch (command) {
            case 'down':
                target.move(1)
                return false
            case 'up':
                target.move(-1)
                return false
            case 'down5X':
                target.move(5)
                return false
            case 'up5X':
                target.move(-5)
                return false
            case 'bottom':
            case 'end':
                target.move(999999)
                return false
            case 'top':
            case 'home':
                target.move(-999999)
                return false
            case 'commit':
                target.enter(null, command)
                return false
            case '1':
            case '2':
            case '3':
            case '4':
            case '5':
            case '6':
            case '7':
            case '8':
                target.enter(+command, command)
                return false
        }
        return true
    }

    return {
        handleKeyEvent,
        handleCommand
    }
}

export default EventDispatcherFactory
