//import g from '../lib/Globals'

function EventDispatcherFactory(options) {
    const extraKeyHandler = options.extraKeyHandler
    const closable = options.closable
    const target = options.target

    const handleKeyEvent = event => {
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
        return false
    }

    const handleCommand = command => {
        console.log('handleCommand', command)
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
                target.enter()
                return false
            case '1':
            case '2':
            case '3':
            case '4':
            case '5':
            case '6':
            case '7':
            case '8':
                target.enter(+command)
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
