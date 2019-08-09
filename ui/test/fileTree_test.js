Feature('FileTree')

Scenario('select file', (I) => {
    I.amOnPage('http://localhost:3179')
    I.waitForElement('.file-tree-node', 5)
    within('.file-tree', () => {
        // click a file
        I.click(locate('.file-tree-node').withText('file_tree.py'))
        I.see('file_tree.py', '.file-tree-node.selected')        
        
        // click another file
        I.click(locate('.file-tree-node').withText('editor.py'))
        I.dontSee('file_tree.py', '.file-tree-node.selected')
    })
    I.seeElement('#panel-left.indicator-on')
})

Scenario('open folder', (I) => {
    within('.file-tree', () => {
        // open folder
        I.doubleClick(locate('.file-tree-node').withText('demo'))
        I.see('demo.py', '.file-tree-node')
        
        // click a file within folder
        I.click(locate('.file-tree-node').withText('jupyter.py'))
        I.dontSee('demo', '.file-tree-node.selected')
    })
})

