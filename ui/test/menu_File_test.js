Feature('Menu-File')

Scenario('open folder', (I) => {
    I.amOnPage('http://localhost:3179')
    I.waitForElement('.file-tree-node', 5)
    
    I.click(locate('.menu-item').withText('File'))
    I.see('Open Folder...')
    
    I.click('#dismiss-popup')
    I.dontSee('Open Folder...')
})