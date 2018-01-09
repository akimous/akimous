import g from '../lib/Globals'
import Keymap from './Keymap'

class LayeredKeyboardControl {
    sendText(text) {
        if (g.activeEditor && g.activeEditor.cm.hasFocus()) {
            g.activeEditor.cm.doc.insertText(text)
        }
    }
    sendEditorCommand(command) {
        this.commandSent = true
        if (g.activeEditor && g.activeEditor.cm.hasFocus()) {
            console.warn('command sent', command)
            g.activeEditor.cm.execCommand(command)
        }
    }
    sendCommand(e) {
        const key = e.key
        this.commandSent = true
        const completionCommand = Keymap.completionCommandKeymap[key]
        if (!g.activeEditor || !g.activeEditor.cm.hasFocus()) return false
        if (completionCommand && g.activeEditor.completion.isOpen) {
            CompletionEventDispatcher.handleCommand(completionCommand)
        } else {
            const extending = e.shiftKey
            if (extending) this.sendEditorCommand('setExtending')
            else this.sendEditorCommand('unsetExtending')
            const command = Keymap.editorCommandKeymap[key.toLowerCase()]
            this.sendEditorCommand(command)

            if (extending) this.sendEditorCommand('unsetExtending')
        }
        return false
    }

    stopPropagation(event) {
        event.preventDefault()
        event.stopPropagation()
        return false
    }
    constructor() {
        this.spacePressed = false
        this.commandSent = false
        this.textSent = false
        const keysRequireHandling = new Set(['Backspace', 'Delete'])
        document.addEventListener('keydown', e => {
            if (e.key === 'Shift') {
                // bypass shift
            } else if (e.key === ' ') {
                this.spacePressed = true
                this.commandSent = false
            } else if (this.spacePressed && !this.textSent && this.commandSent &&
                (e.key.length === 1 || keysRequireHandling.has(e.key))) {
                this.sendCommand(e)
            } else if (this.spacePressed) {
                this.textSent = false
            } else {
                this.textSent = true
                return CompletionEventDispatcher.handleNormalModeEvent(e)
            }
            return this.stopPropagation(e)
        }, {
            capture: true
        })

        document.addEventListener('keyup', e => {
            if (e.key === 'Shift') {
                // bypass shift
            } else if (e.key === ' ') {
                this.spacePressed = false
                if (!this.commandSent) {
                    CompletionEventDispatcher.handleCommand('commit') || this.sendText(' ')
                }
                return this.stopPropagation(e)
            } else if (this.spacePressed && !this.textSent && !this.commandSent &&
                (e.key.length === 1 || keysRequireHandling.has(e.key))) {
                this.sendCommand(e)
                return this.stopPropagation(e)
            } else if (!this.commandSent && !this.textSent) {
                this.sendText(e.key)
                this.textSent = true
            }
        }, {
            capture: true
        })
    }
}

export default LayeredKeyboardControl
