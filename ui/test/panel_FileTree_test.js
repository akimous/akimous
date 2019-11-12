Feature('FileTree')

Scenario('select file', (I) => {
    I.amOnPage('http://localhost:3178')
    I.waitForElement('.file-tree-node', 5)
    within('.file-tree', () => {
        // click a file
        I.click(locate('.file-tree-node').withText('LICENSE'))
        I.see('LICENSE', '.file-tree-node.selected')        
        
        // click another file
        I.click(locate('.file-tree-node').withText('CHANGELOG.md'))
        I.dontSee('LICENSE', '.file-tree-node.selected')
    })
    I.seeElement('#panel-left.indicator-on')
})

Scenario('open folder', (I) => {
    within('.file-tree', async () => {
        // open folder
        await I.doubleClickAlt('akimous', '.display-name')
        I.wait(1)
        I.see('__init__.py', '.file-tree-node')
        
        // click a file within folder
        I.click(locate('.file-tree-node').withText('__main__.py'))
        I.dontSee('akimous', '.file-tree-node.selected')
    })
})

