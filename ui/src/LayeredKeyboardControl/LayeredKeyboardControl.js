import g from '../lib/Globals'
import { config } from '../lib/ConfigManager'
import KeyMap from './Keymap'
import CodeEditor from '../editor/CodeEditor.html'

export function togglePanelAutoHide(panel) {
    const autoHide = !panel.autoHide
    panel.$set({
        autoHide,
        hidden: autoHide
    })
    if (autoHide) g.setFocus([g.panelMiddle])
}

class LayeredKeyboardControl {
    sendEditorCommand(command) {
        this.commandSent = true
        if (g.activeEditor && g.activeEditor.cm.hasFocus()) {
            try {
                g.activeEditor.cm.execCommand(command)
            } catch (e) {
                console.error(e)
            }
        }
    }
    sendCommand(e) {
        // return true if not handled or allowed to propagate
        const code = e.code
        let key = code
        if (code.startsWith('Key'))
            key = code.substring(3)
        this.commandSent = true
        const command = KeyMap.genericCommandKeyMap[code]
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
                        const editorCommand = KeyMap.editorCommandKeyMap[code]
                        if (!editorCommand) continue
                        if (extending) this.sendEditorCommand('setExtending')
                        else this.sendEditorCommand('unsetExtending')
                        this.sendEditorCommand(editorCommand)
                        if (extending) this.sendEditorCommand('unsetExtending')
                        g.keyboardControlHint.showDescription(key)
                        g.keyboardControlHint.highlight(key)
                        return false
                    } else {
                        const handler = focus.keyEventHandler
                        if (handler === undefined) continue
                        const shouldPropagate = handler.handleCommand(command, focus)
                        if (shouldPropagate) continue
                        g.keyboardControlHint.showDescription(key)
                        g.keyboardControlHint.highlight(key)
                        return false
                    }
                }
                return true
        }
        g.keyboardControlHint.showDescription(key)
        g.keyboardControlHint.highlight(key)
    }
    stopPropagation(event) {
        event.preventDefault()
        event.stopPropagation()
        return false
    }
    set macroMode(x) {
        this._macroMode = x
        if (x) {
            this._previousPanelRightView = g.panelRight.focus
            g.macro.active = true
        } else {
            this._previousPanelRightView && g.panelRight.activateView(this._previousPanelRightView)
        }
    }
    get macroMode() {
        return this._macroMode
    }
    constructor() {
        this.enabled = config.keymap.layeredKeyboardControl
        this.commandSent = false
        let spacePressed = false
        let textSent = false
        this._macroMode = false
        let composeTimeStamp = 0
        const keysRequireHandling = new Set(['Backspace', 'Delete'])

        this._keydown = e => {
            if (!this.enabled) return true
            if (e.isComposing) return true // do not interfere with IME
            switch (e.key) {
                case 'Shift':
                    return true
                    // break // this will interfere with hotkey
                case ' ':
                    if (spacePressed) break // ignore duplicated keydown events
                    if (g.focus.allowWhiteSpace) return true
                    spacePressed = true
                    this.commandSent = false
                    g.keyboardControlHint.highlightModifier('Space')
                    break
                case 'Control':
                    if (e.metaKey) {
                        this.macroMode = true
                        g.tabNumber.$set({ active: false })
                    } else
                        g.tabNumber.$set({ active: true })
                    return true // let it propagate
                case 'Meta':
                    if (e.ctrlKey) {
                        this.macroMode = true
                        g.tabNumber.$set({ active: false })
                    } else
                        g.tabNumber.$set({ active: true })
                    return true // let it propagate
                case 'Tab':
                    // When completion window is open, commit selection instead of increasing indent
                    if (g.activeEditor.completion.open) {
                        g.activeEditor.completion.enter(null, 'Tab')
                        return this.stopPropagation(e)
                    }
                    return true // let it propagate
                default:
                    if (this.macroMode) {
                        g.macro.dispatchMacro(e)
                        return this.stopPropagation(e)
                    } else if (spacePressed && !textSent && this.commandSent &&
                        (e.key.length === 1 || keysRequireHandling.has(e.key))) {
                        this.sendCommand(e)
                    } else if (spacePressed) {
                        textSent = false
                    } else if ((e.metaKey || e.ctrlKey) && !isNaN(e.key)) { // switch tab
                        const focusedPanel = g.focusStack[0]
                        if (focusedPanel)
                            focusedPanel.tabBar.switchToTab(+e.key)
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
                        // Handle "cut" event
                        // Cut event is handled via command-X hotkey,
                        // because we cannot get the content just cut on the cut event.
                        if (e.key === 'x' && (e.metaKey || e.ctrlKey) && g.activeEditor) {
                            const cm = g.activeEditor.cm
                            let selection = cm.getSelection()
                            if (!selection) selection = cm.getLine(cm.getCursor().line) + '\n'
                            g.macro.addClipboardItem(selection)
                        }
                        return true // if not handled, just propagate
                    }
            }
            return this.stopPropagation(e)
        }
        
        this._keyup = e => {
            if (!this.enabled) return true
            if (e.isComposing) return true // do not interfere with IME
            if (!g.focus) {
                console.warn('no focus')
                return true
            }
            switch (e.key) {
                case 'Shift':
                    if (!g.activeEditor) break
                    g.activeEditor.cm.display.shift = false
                    return true
                    // break // this will interfere with hotkey
                case ' ': {
                    const { focus } = g
                    spacePressed = false
                    if (focus.allowWhiteSpace) return true
                    if (!this.commandSent && this.sendCommand(e)) { // sendCommand is used by completion, do not remove
                        if (focus.constructor.name === 'CodeEditor') {
                            // avoid insert extra space after IME commit
                            if (g.activeEditor && e.timeStamp - composeTimeStamp > 200) { 
                                g.activeEditor.insertText(' ')
                            }
                        } else if (focus.input) {
                            const { input } = focus
                            const { value, selectionStart, selectionEnd } = input
                            input.value = `${value.substring(0, selectionStart)} ${value.substring(selectionEnd)}`
                            input.setSelectionRange(selectionEnd + 1, selectionEnd + 1)
                        }
                    }
                    g.keyboardControlHint.dimModifier('Space')
                    return this.stopPropagation(e)
                }
                case 'Control':
                    g.tabNumber.$set({ active: false })
                    this.macroMode = false
                    return true // let it propagate
                case 'Meta':
                    g.tabNumber.$set({ active: false })
                    this.macroMode = false
                    return true // let it propagate
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
        }
        
        this._composition = e => {
            composeTimeStamp = e.timeStamp
        }
        document.addEventListener('keydown', this._keydown, { capture: true })
        document.addEventListener('keyup', this._keyup, { capture: true })
        document.addEventListener('compositionstart', this._composition)
        document.addEventListener('compositionend', this._composition)
        document.addEventListener('compositionupdate', this._composition)
    }
    
    destroy() {
        document.removeEventListener('keydown', this._keydown, true)
        document.removeEventListener('keyup', this._keyup, true)
        document.removeEventListener('compositionstart', this._composition)
        document.removeEventListener('compositionend', this._composition)
        document.removeEventListener('compositionupdate', this._composition)
    }
}

export default LayeredKeyboardControl
