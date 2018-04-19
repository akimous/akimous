import keyboardJS from 'keyboardjs'
import g from '../lib/Globals'

function bindHotkeys() {
    function hotkey(key, handler) {
        keyboardJS.bind(key, e => {
            e.preventDefault()
            return handler(e)
        })
    }

    hotkey('mod + s', g.saveFile)

    hotkey('mod + shift + s', () => {
        g.saveAll()
    })

    hotkey('mod + `', () => {
        if (!g.activeEditor) return
        const { filePath } = g.activeEditor.get()
        filePath && g.panelMiddle.closeFile(filePath)
    })

    const canBeRenamed = token => {
        return token.string.length > 0 && token.type &&
            (token.type.includes('variable') || token.type.includes('def'))
    }
    hotkey('f6', () => {
        const editor = g.activeEditor
        if (!editor) return
        const cm = editor.cm
        const cursor = cm.getCursor('to')
        let token = cm.getTokenAt(cursor)
        if (!canBeRenamed(token)) {
            cursor.ch += 1
            token = cm.getTokenAt(cursor)
        }
        if (!canBeRenamed(token)) {
            g.notificationBar.show('warning', 'Please select a variable.')
            return
        }
        editor.ws.send({
            cmd: 'findUsages',
            line: cursor.line,
            ch: cursor.ch,
            token: token.string
        })
    })
}
export default {
    bindHotkeys
}
