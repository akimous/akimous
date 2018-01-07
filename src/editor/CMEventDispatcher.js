import g from '../lib/Globals.js'

class CMEventDispatcher {
    constructor(editor) {
        const cm = editor.cm
        const doc = cm.doc
        doc.on('change', (doc, changeObj) => {
            if (editor.clean === doc.isClean()) return
            editor.clean = !editor.clean
            g.tabBar.pathToTab[editor.get('filePath')].set({
                clean: editor.clean
            })
        })
    }
}

export default CMEventDispatcher
