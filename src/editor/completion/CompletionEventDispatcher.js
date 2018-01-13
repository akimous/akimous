import g from '../../lib/Globals'
class CompletionEventDispatcher {
    static handleNormalModeEvent(event) {
//        const editor = g.activeEditor.editor
        const completion = g.activeEditor.completion

        if (!completion.isOpen) return true
        switch (event.key) {
            case 'ArrowDown':
                completion.down()
                console.log('handled')
                break
            case 'ArrowUp':
                completion.up()
                break

            case 'Escape':
                completion.close()
                break
            case 'ArrowLeft':
            case 'ArrowRight':
                completion.close()
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
                    completion.close()
                return true
        }
        event.preventDefault()
        event.stopPropagation()
        return false
    }

    static handleCommand(command) {
//        const editor = g.activeEditor.editor
        const completion = g.activeEditor.completion

        if (!completion.isOpen) return false
        switch (command) {
            case 'down':
                completion.down()
                return true
            case 'up':
                completion.up()
                return true
            case 'down5X':
                for (let i = 0; i < 5; i++)
                    completion.down()
                return true
            case 'up5X':
                for (let i = 0; i < 5; i++)
                    completion.up()
                return true
            case 'commit':
                completion.commit()
                return true
        }
        console.error('unhandled completion command')
    }
}

export default CompletionEventDispatcher
