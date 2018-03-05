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
            console.warn('command sent', command)
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
                if (g.focus instanceof CodeEditor) {
                    const extending = e.shiftKey
                    if (extending) this.sendEditorCommand('setExtending')
                    else this.sendEditorCommand('unsetExtending')
                    this.sendEditorCommand(Keymap.editorCommandKeymap[code])
                    if (extending) this.sendEditorCommand('unsetExtending')
                } else if (g.focus instanceof Completion) {
                    this.completionKeyHandler.handleCommand(command)
                } else if (g.focus instanceof ContextMenu) {
                    this.contextMenuKeyHandler.handleCommand(command)
                }
        }
        //        if (!g.activeEditor || !g.activeEditor.cm.hasFocus()) {
        //            if (command)
        //                this.contextMenuKeyHandler.handleCommand(command)
        //            return false
        //        }
        //        if (command && g.activeEditor.completion.get('open')) {
        //            this.completionKeyHandler.handleCommand(command)
        //        } else {
        //            const extending = e.shiftKey
        //            if (extending) this.sendEditorCommand('setExtending')
        //            else this.sendEditorCommand('unsetExtending')
        //            const command = Keymap.editorCommandKeymap[code]
        //            this.sendEditorCommand(command)
        //            if (extending) this.sendEditorCommand('unsetExtending')
        //        }
        //        return false
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

        this.completionKeyHandler = EventDispatcherFactory({
//            dispatchTarget: ['activeEditor', 'completion'],
            extraKeyHandler(event, target) {
                if (/[.,()[\]:+\-*/|&^~%@><!]/.test(event.key))
                    target.enter()
                else if (/[=[\](){}]/.test(event.key))
                    target.set({
                        open: false
                    })
                return true
            }
        })
        this.contextMenuKeyHandler = EventDispatcherFactory({
//            dispatchTarget: ['contextMenu'],
        })

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
                return this.completionKeyHandler.handleKeyEvent(e) &&
                    this.contextMenuKeyHandler.handleKeyEvent(e)
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
                    this.completionKeyHandler.handleCommand('commit') ||
                        this.contextMenuKeyHandler.handleCommand('commit') ||
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
