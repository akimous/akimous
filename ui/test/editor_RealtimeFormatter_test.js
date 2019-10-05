Feature('Realtime Formatter')

Scenario('Normal formatting', (I) => {
    I.amOnPage('http://localhost:3179')
    I.wait(1)
    I.waitForElement('.file-tree-node', 5)
    I.click('pre.CodeMirror-line')

    const specialKeys = new Set(['Enter', 'Space'])
    const typeAndCompare = (inputs, displays) => {
        for (const i of inputs) {
            if (Array.isArray(i)) {
                I.type(i)
            } else if (specialKeys.has(i)) {
                I.pressKey(i)
            } else {
                for (const j of i) {
                    I.pressKey(j)
                }
            }
        }
        if (!displays) return
        for (const i of displays) {
            I.see(i)
        }
    }
    const clear = () => {
        I.type(['Escape'])
        I.type(['Meta', 'a'])
        I.type(['Backspace'])
    }
    
    typeAndCompare(['for i in range(5', ['Meta', 'Enter'], 'print(i'],
        ['for i in range(5):', 'print(i)'])
    I.dontSee('pprint')
    clear()
    
    typeAndCompare(['for i in ra', ['Escape']])
    typeAndCompare(['ng '], ['range()'])
    clear()
    
    typeAndCompare(['fr '], ['from'])
    typeAndCompare(['sph'])
    I.wait(3)
    typeAndCompare(['.'], ['from sphinx.'])
    typeAndCompare(['io im '], ['from sphinx.io import '])
    typeAndCompare(['rea', ['Enter']], ['from sphinx.io import read_doc'])
    clear()
    
    typeAndCompare(['"""classbla', ['Meta', 'Enter'], 'cla'])
    I.dontSee('classbla', '.row-content')
    clear()
    
    typeAndCompare(['cla Bla', ['Enter']], ['class Bla:'])
    typeAndCompare(['de', ['Space', '2'], ['Enter']], ['    def __init__(self):'])
    typeAndCompare(['pas', ['Meta', 'Enter']], ['        pass'])
    typeAndCompare(['def'])
    I.dontSee('def __init__', '.row-content')
    clear()
    
    // pause()
})
