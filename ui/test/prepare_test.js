// Run before any test to setup environment
Feature('Prepare')

Scenario('Preparing', async (I) => {
    await I.amOnPage('http://localhost:3178')
    await I.wait(1)
    I.click('.path > .text-input > input')
    for (let i = 0; i < 50; i++)
        I.type(['Backspace'])
    I.type(['Enter'])
    I.click('.button.open')
    await I.wait(1)
    await I.waitForElement('.file-tree-node', 5)
    await I.wait(.5)
    
    await I.doubleClickAlt('tests', '.display-name')
    await I.wait(.5)
    await I.doubleClickAlt('fixture', '.display-name')
    await I.wait(.5)
    await I.doubleClickAlt('empty.py', '.display-name')
    
    await I.wait(1)
    await I.click('pre.CodeMirror-line')
})
