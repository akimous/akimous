import g from '../../lib/Globals'
class CompletionEventDispatcher {
    static handleNormalModeEvent(event) {
        const completion = g.activeEditor.completion
        if (!completion.get('open')) return true
        switch (event.key) {
            case 'ArrowDown':
                completion.move(1)
                break
            case 'ArrowUp':
                completion.move(-1)
                break

            case 'Escape':
                completion.set({
                    open: false
                })
                break
            case 'ArrowLeft':
            case 'ArrowRight':
                completion.set({
                    open: false
                })
                return true

            case ' ':
                completion.commit()
                break
            case '.':
            case ',':
            case '(':
            case ')':
            case '[':
            case ']':
            case ':':
            case 'Enter':
                completion.commit()
                return true

            default:
                if (/[+\-\*/|&^~%@><!]/.test(event.key))
                    completion.commit()
                else if (/[=\[\](){}]/.test(event.key))
                    completion.set({
                        open: false
                    })
                return true
        }
        event.preventDefault()
        event.stopPropagation()
        return false
    }

    static handleCommand(command) {
        const completion = g.activeEditor.completion
        if (!completion.get('open')) return false
        switch (command) {
            case 'down':
                completion.move(1)
                return true
            case 'up':
                completion.move(-1)
                return true
            case 'down5X':
                completion.move(5)
                return true
            case 'up5X':
                completion.move(-5)
                return true
            case 'bottom':
                completion.move(9999)
                return true
            case 'top':
                completion.move(-9999)
                return true
            case 'commit':
                completion.commit()
                return true
            case '1':
            case '2':
            case '3':
            case '4':
            case '5':
            case '6':
            case '7':
            case '8':
                completion.commit(+command)
                return true
        }
        console.error('unhandled completion command')
    }
}

export default CompletionEventDispatcher
