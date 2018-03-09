import g from '../lib/Globals'
import Keymap from './Keymap'
import EventDispatcherFactory from './EventDispatcherFactory'
import CodeEditor from '../editor/CodeEditor.html'
import Completion from '../editor/completion/Completion.html'
import ContextMenu from '../lib/ContextMenu.html'

class LayeredKeyboardControl {
    sendEditorCommand(command) {
        this.commandSent = true
        if (g.activeEditor && g.activeEditor.cm.hasFocus()) {
            g.activeEditor.cm.execCommand(command)
        }
    }
    sendCommand(e) {
        const code = e.code
        this.commandSent = true
        const command = Keymap.genericCommandKeymap[code]
        switch (command) {
            case 'panelLeft':
                g.setFocus([g.panelLeft])
                break
            case 'panelMiddle':
                g.setFocus([g.panelMiddle])
                break
            case 'panelRight':
                g.setFocus([g.panelRight])
                break
            default:
                for (let i = g.focusStack.length - 1; i >= 0; i--) {
                    const focus = g.focusStack[i]
                    if (focus instanceof CodeEditor) {
                        const extending = e.shiftKey
                        const editorCommand = Keymap.editorCommandKeymap[code]
                        if (!editorCommand) continue
                        if (extending) this.sendEditorCommand('setExtending')
                        else this.sendEditorCommand('unsetExtending')
                        this.sendEditorCommand(editorCommand)
                        if (extending) this.sendEditorCommand('unsetExtending')
                        return false
                    } else {
                        const handler = focus.keyEventHandler
                        if (handler === undefined) continue
                        const shouldPropagate = handler.handleCommand(command)
                        if (shouldPropagate) continue
                        return false
                    }
                }
                return true
        }
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
                for (let i = g.focusStack.length - 1; i >= 0; i--) {
                    const handler = g.focusStack[i].keyEventHandler
                    if (handler === undefined) continue
                    const shouldPropagate = handler.handleKeyEvent(e)
                    if (shouldPropagate) continue
                    return this.stopPropagation(e)
                }
                return true // if not handled, just propagate
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
                if (!this.commandSent) 
                    this.sendCommand(e) && g.activeEditor.insertText(' ')
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
