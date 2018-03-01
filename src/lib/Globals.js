let _uid = 0
const g = {
    focusStack: [],
    get focus() {
        const stack = this.focusStack
        return stack[stack.length - 1]
    },
    setFocus(x) {
        const root = x[0]
        const focusStack = this.focusStack
        for (let i = 0; i < focusStack.length; i++) {
            if (focusStack[i] === root) {
                focusStack.splice(i, 9999, ...x)
                return this.onFocusChanged()
            }
        }
        this.focusStack = x
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
