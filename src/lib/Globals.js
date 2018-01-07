const g = {
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
    }
}

export default g
