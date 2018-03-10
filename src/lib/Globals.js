import Completion from '../editor/completion/Completion.html'
import ContextMenu from './ContextMenu.html'
import PanelMiddle from '../PanelMiddle.html'

let _uid = 0
const g = {
    focusStack: [],
    get focus() {
        const stack = this.focusStack
        return stack[stack.length - 1]
    },
    setFocus(x) {
        const focusStack = this.focusStack

        // backup original focus stack
        const originalRoot = focusStack[0]
        if (originalRoot && originalRoot !== x[0] && focusStack.length > 1) {
            if (this.focus instanceof Completion || this.focus instanceof ContextMenu) {
                this.focus.set({
                    open: false
                })
            }
            originalRoot.set({
                focusStack: focusStack.slice(1)
            })
            
            // if we don't force refresh CM on Safari, it will not show panelMiddle indicator
            // try remove this if newer versions of Safari fix this
            if (x[0] instanceof PanelMiddle && this.activeEditor) {
                window.requestAnimationFrame(() => {
                    this.activeEditor.cm.refresh()
                })
            }
        }

        this.focusStack = x
        // restore focus stack
        if (x.length === 1) {
            const originalFocusStack = x[0].get('focusStack')
            originalFocusStack && this.focusStack.push(...originalFocusStack)
        }
        this.onFocusChanged()
    },
    pushFocus(x) {
        const focusStack = this.focusStack
        for (let i = 0; i < focusStack.length; i++) {
            if (focusStack[i] === x) return
        }
        focusStack.push(x)
        this.onFocusChanged()
    },
    popFocus(x) {
        const focusStack = this.focusStack
        for (let i = focusStack.length - 1; i >= 0; i--) {
            if (focusStack[i] === x) {
                focusStack.splice(i, 9999)
                return this.onFocusChanged()
            }
        }
    },
    onFocusChanged() {
        console.warn('focus changed', this.focusStack)
        const focusedPanel = this.focusStack[0]
        for (const panel of [g.panelLeft, g.panelMiddle, g.panelRight]) {
            panel && panel.set({
                focused: panel === focusedPanel
            })
        }
    },
    saveFile() {
        g.activeEditor && g.activeEditor.save()
    },
    saveAll() {
        console.log('saveAll')
        const pathToEditor = g.panelMiddle.pathToEditor
        for (let path in pathToEditor) {
            const editor = pathToEditor[path]
            if (!editor.clean)
                editor.save()
        }
    },
    get uid() {
        return _uid++
    }
}
window.g = g
export default g
