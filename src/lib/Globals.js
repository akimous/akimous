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
                console.warn('focus changed', this.focusStack)
                return
            }
        }
        this.focusStack = x
        console.warn('focus changed', this.focusStack)
    },
    pushFocus(x) {
        const focusStack = this.focusStack
        for (let i = 0; i < focusStack.length; i++) {
            if (focusStack[i] === x) return
        }
        focusStack.push(x)
        console.warn('focus changed', this.focusStack)
    },
    popFocus(x) {
        const focusStack = this.focusStack
        for (let i = focusStack.length - 1; i >= 0; i--) {
            if (focusStack[i] === x) {
                focusStack.splice(i, 9999)
                console.warn('focus changed', this.focusStack)
                return
            }
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
