Feature('FileTree')

Scenario('select file', (I) => {
    I.amOnPage('http://google.com')
    I.amOnPage('http://localhost:3179')
    within('.file-tree', () => {
        I.click(locate('.file-tree-node').withText('file_tree.py'))
        I.see('file_tree.py', '.file-tree-node.selected')        
        
        I.click(locate('.file-tree-node').withText('editor.py'))
        I.dontSee('file_tree.py', '.file-tree-node.selected')
    })
    I.seeElement('#panel-left.indicator-on')
})
