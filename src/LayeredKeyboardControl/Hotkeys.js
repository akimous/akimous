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
        const filePath = g.activeEditor.get('filePath')
        filePath && g.panelMiddle.closeFile(filePath)
    })
}
export default {
    bindHotkeys
}
