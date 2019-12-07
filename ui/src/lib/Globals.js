let _uid = 0
const g = {
    dev: window.location.href.includes('dev=1'),
    focusStack: [],
    get focus() {
        const stack = this.focusStack
        // console.log('got focus', stack[stack.length - 1], stack)
        return stack[stack.length - 1]
    },
    setFocus(x) {
        // console.warn('set focus', x)
        const focusStack = this.focusStack
        // backup original focus stack
        const oldRoot = focusStack[0]
        const newRoot = x[0]

        // if focused panel is changed
        if (oldRoot && oldRoot !== x[0]) {
            // hide panel if autoHide is true and losing focus
            if (oldRoot.autoHide)
                oldRoot.$set({ hidden: true })
            newRoot.$set({ hidden: false })
            // store focus stack if needed
            if (focusStack.length > 1) {
                if (this.focus.constructor.name === 'Completion' ||
                    this.focus.constructor.name === 'ContextMenu') {
                    this.focus.$set({ open: false })
                }
                oldRoot.$set({
                    focusStack: focusStack.slice(1)
                })
            }
        }
        this.focusStack = x
        // restore focus stack
        if (x.length === 1) {
            const originalFocusStack = x[0].focusStack
            originalFocusStack && this.focusStack.push(...originalFocusStack)
        }
        this.onFocusChanged()
    },
    pushFocus(x) {
        const focusStack = this.focusStack
        if (focusStack.includes(x)) return
        focusStack.push(x)
        this.onFocusChanged()
    },
    popFocus(x) {
        // console.log('pop focus', x)
        const focusStack = this.focusStack
        for (let i = focusStack.length - 1; i >= 0; i--) {
            if (focusStack[i] === x) {
                focusStack.splice(i, 9999)
                return this.onFocusChanged()
            }
        }
    },
    onFocusChanged() {
        const focusedPanel = this.focusStack[0]
        for (const panel of [g.panelLeft, g.panelMiddle, g.panelRight]) {
            if (!panel) break
            panel.$set({
                focused: panel === focusedPanel
            })
        }
    },
    close() {
        if (!g.activeEditor) return
        const { filePath } = g.activeEditor
        filePath && g.panelMiddle.closeFile(filePath)
    },
    closeAll() {
        if (!g.activeEditor) return
        const { editors } = g.panelMiddle
        for (let path in editors) {
            const editor = editors[path]
            if (editor && editor.clean)
                g.panelMiddle.closeView(editor)
        }
    },
    saveFile() {
        g.activeEditor && g.activeEditor.save()
    },
    saveAll() {
        const pathToEditor = g.panelMiddle.pathToEditor
        for (let path in pathToEditor) {
            const editor = pathToEditor[path]
            if (!editor.clean)
                editor.save()
        }
    },
    CMCommand(command) {
        if (!g.activeEditor) return
        const { cm } = g.activeEditor
        if (!cm) return
        cm.execCommand(command)
    },
    get uid() {
        return _uid++
    },
}
window.g = g
export default g
