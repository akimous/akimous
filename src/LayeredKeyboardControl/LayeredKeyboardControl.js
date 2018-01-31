import g from '../lib/Globals'
import Keymap from './Keymap'
import CompletionEventDispatcher from '../editor/completion/CompletionEventDispatcher.js'
import ContextMenuEventDispatcher from '../lib/ContextMenuEventDispatcher.js'

class LayeredKeyboardControl {
    sendEditorCommand(command) {
        this.commandSent = true
        if (g.activeEditor && g.activeEditor.cm.hasFocus()) {
            console.warn('command sent', command)
            g.activeEditor.cm.execCommand(command)
        }
    }
    sendCommand(e) {
        const code = e.code
        this.commandSent = true
        const completionCommand = Keymap.completionCommandKeymap[code]
        if (!g.activeEditor || !g.activeEditor.cm.hasFocus()) {
            if (completionCommand)
                ContextMenuEventDispatcher.handleCommand(completionCommand)
            return false
        }
        if (completionCommand && g.activeEditor.completion.get('open')) {
            CompletionEventDispatcher.handleCommand(completionCommand)
        } else {
            const extending = e.shiftKey
            if (extending) this.sendEditorCommand('setExtending')
            else this.sendEditorCommand('unsetExtending')
            const command = Keymap.editorCommandKeymap[code]
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
                return CompletionEventDispatcher.handleNormalModeEvent(e) &&
                    ContextMenuEventDispatcher.handleNormalModeEvent(e)
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
                    CompletionEventDispatcher.handleCommand('commit') ||
                        ContextMenuEventDispatcher.handleCommand('commit') ||
                        g.activeEditor.insertText(' ')
                }
                return this.stopPropagation(e)
            } else if (this.spacePressed && !this.textSent && !this.commandSent &&
                (e.key.length === 1 || keysRequireHandling.has(e.key))) {
                this.sendCommand(e)
                return this.stopPropagation(e)
            } else if (!this.commandSent && !this.textSent) {
                g.activeEditor.insertText(e.key)
                this.textSent = true
            }
        }, {
            capture: true
        })
    }
}

export default LayeredKeyboardControl
