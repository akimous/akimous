import g from './Globals'
class ContextMenuEventDispatcher {
    static handleNormalModeEvent(event) {
        const menu = g.contextMenu
        if (!menu.get('open')) return true
        switch (event.key) {
            case 'ArrowDown':
                menu.move(1)
                break
            case 'ArrowUp':
                menu.move(-1)
                break

            case 'Escape':
                menu.set({
                    open: false
                })
                break

            case ' ':
            case 'Enter':
                menu.get('selectedRow').click()
                break

            default:
                return true
        }
        event.preventDefault()
        event.stopPropagation()
        return false
    }

    static handleCommand(command) {
        const menu = g.contextMenu

        if (!menu.get('open')) return false
        switch (command) {
            case 'down':
                menu.move(1)
                return true
            case 'up':
                menu.move(-1)
                return true
            case 'down5X':
                menu.move(5)
                return true
            case 'up5X':
                menu.move(-5)
                return true
            case 'bottom':
                menu.move(9999)
                return true
            case 'top':
                menu.move(-9999)
                return true
            case 'commit':
                menu.get('selectedRow').click()
                return true
            case '1':
            case '2':
            case '3':
            case '4':
            case '5':
            case '6':
            case '7':
            case '8':
                const i = +command
                if (i < menu.rows.length)
                    menu.rows[i - 1].click()
                return true
        }
        console.error('unhandled context menu command')
    }
}

export default ContextMenuEventDispatcher
