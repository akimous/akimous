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
        for (const i of displays) {
            I.see(i)
        }
    }

    typeAndCompare(['for i in range(5', ['Meta', 'Enter'], 'print(i'],
        ['for i in range(5):', 'print(i)'])
    I.dontSee('pprint')
    pause()
})
