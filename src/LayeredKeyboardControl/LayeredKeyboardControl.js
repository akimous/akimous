import g from '../lib/Globals'
import Keymap from './Keymap'
import CodeEditor from '../editor/CodeEditor.html'

function togglePanelAutoHide(panel) {
    const autoHide = !panel.get('autoHide')
    panel.set({
        autoHide,
        hidden: autoHide
    })
    if (autoHide) g.setFocus([g.panelMiddle])
}

class LayeredKeyboardControl {
    sendEditorCommand(command) {
        this.commandSent = true
        if (g.activeEditor && g.activeEditor.cm.hasFocus()) {
            g.activeEditor.cm.execCommand(command)
        }
    }
    sendCommand(e) {
        // return true if not handled or allowed to propagate
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
            case 'togglePanelLeft':
                togglePanelAutoHide(g.panelLeft)
                break
            case 'togglePanelRight':
                togglePanelAutoHide(g.panelRight)
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
                        const shouldPropagate = handler.handleCommand(command, focus)
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
        this.commandSent = false
        let spacePressed = false
        let textSent = false
        let composeTimeStamp = 0
        const keysRequireHandling = new Set(['Backspace', 'Delete'])

        document.addEventListener('keydown', e => {
            if (e.isComposing) return true // do not interfere with IME
            switch (e.key) {
                case 'Shift':
                    break
                case 'Meta':
                case 'Control':
                    g.tabNumber.set({
                        active: true
                    })
                    return true // let it propagate
                case ' ':
                    if (g.focus.get('allowWhiteSpace')) return true
                    spacePressed = true
                    this.commandSent = false
                    break
                default:
                    if (spacePressed && !textSent && this.commandSent &&
                        (e.key.length === 1 || keysRequireHandling.has(e.key))) {
                        this.sendCommand(e)
                    } else if (spacePressed) {
                        textSent = false
                    } else if ((e.metaKey || e.ctrlKey) && !isNaN(e.key)) { // switch tab
                        const focusedPanel = g.focusStack[0]
                        if (focusedPanel)
                            focusedPanel.tabBar.switchToTab(+e.key + 1) // resizeSensor counts 1
                        return this.stopPropagation(e)
                    } else {
                        textSent = true
                        for (let i = g.focusStack.length - 1; i >= 0; i--) {
                            const target = g.focusStack[i]
                            const handler = target.keyEventHandler
                            if (handler === undefined) continue
                            const shouldPropagate = handler.handleKeyEvent(e, target)
                            if (shouldPropagate) continue
                            return this.stopPropagation(e)
                        }
                        return true // if not handled, just propagate
                    }
            }
            return this.stopPropagation(e)
        }, {
            capture: true
        })

        document.addEventListener('keyup', e => {
            if (e.isComposing) return true // do not interfere with IME
            switch (e.key) {
                case 'Shift':
                    break
                case 'Meta':
                case 'Control':
                    if (!e.metaKey && !e.ctrlKey)
                        g.tabNumber.set({
                            active: false
                        })
                    return true // let it propagate
                case ' ':
                    spacePressed = false
                    if (g.focus.get('allowWhiteSpace')) return true
                    if (!this.commandSent && this.sendCommand(e) &&
                        e.timeStamp - composeTimeStamp > 200) { // avoid insert extra space after IME commit
                        g.activeEditor.insertText(' ')
                    }
                    return this.stopPropagation(e)
                default:
                    if (spacePressed && !textSent && !this.commandSent &&
                        (e.key.length === 1 || keysRequireHandling.has(e.key))) {
                        this.sendCommand(e)
                        return this.stopPropagation(e)
                    } else if (!this.commandSent && !textSent &&
                        e.key.length === 1 && !e.metaKey && !e.ctrlKey) {
                        textSent = true
                        g.activeEditor.insertText(e.key)
                    }
            }
        }, {
            capture: true
        })

        document.addEventListener('compositionstart', e => {
            composeTimeStamp = e.timeStamp
        })
        document.addEventListener('compositionend', e => {
            composeTimeStamp = e.timeStamp
        })
        document.addEventListener('compositionupdate', e => {
            composeTimeStamp = e.timeStamp
        })
    }
}

export default LayeredKeyboardControl
