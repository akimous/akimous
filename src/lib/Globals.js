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
        const oldRoot = focusStack[0]
        const newRoot = x[0]

        // if focused panel is changed
        if (oldRoot && oldRoot !== x[0]) {
            // hide panel if autoHide is true and losing focus
            if (oldRoot.get().autoHide)
                oldRoot.set({
                    hidden: true
                })
            newRoot.set({
                hidden: false
            })

            // store focus stack if needed
            if (focusStack.length > 1) {
                if (this.focus.constructor.name === 'Completion' ||
                    this.focus.constructor.name === 'ContextMenu') {
                    this.focus.set({
                        open: false
                    })
                }
                oldRoot.set({
                    focusStack: focusStack.slice(1)
                })
            }
        }

        this.focusStack = x
        // restore focus stack
        if (x.length === 1) {
            const originalFocusStack = x[0].get().focusStack
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
        //         console.warn('focus changed', this.focusStack)
        const focusedPanel = this.focusStack[0]
        for (const panel of [g.panelLeft, g.panelMiddle, g.panelRight]) {
            if (!panel) break
            panel.set({
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
    },
}
window.g = g
export default g
