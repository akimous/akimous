Feature('Realtime Formatter')

Scenario('Normal formatting', (I) => {
    I.amOnPage('http://localhost:3179')
    I.wait(1)
    I.waitForElement('.file-tree-node', 5)
    I.click('pre.CodeMirror-line')

    const specialKeys = new Set(['Enter', 'Space'])
    const typeAndCompare = (inputs, displays) => {
        for (const i of inputs) {
            let first = true
            if (Array.isArray(i)) {
                I.type(i)
            } else if (specialKeys.has(i)) {
                I.pressKey(i)
            } else {
                for (const j of i) {
                    if (!/[0-9a-zA-Z]/.test(j)){
                        I.wait(.3)
                        I.pressKey(j)
                        I.wait(.2)
                    } else if (first) {
                        I.pressKey(j)
                        I.wait(.3)
                        first = false
                    } else {
                        I.pressKey(j)
                    }
                }
            }
        }
        if (!displays) return
        I.wait(.5)
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
    
    typeAndCompare(['fr s'], ['from'])
    I.wait(1)
    typeAndCompare(['ph'])
    typeAndCompare(['.'], ['from sphinx.'])
    typeAndCompare(['io im '], ['from sphinx.io import '])
    typeAndCompare(['rea', ['Enter']], ['from sphinx.io import read_doc'])
    clear()
    
    typeAndCompare(['"""classbla', ['Meta', 'Enter'], 'cla'])
    I.dontSee('classbla', '.row-content')
    clear()
    
    typeAndCompare(['cla C', ['Enter']], ['class C:']) // single character class
    clear()
    
    typeAndCompare(['cla Bla', ['Enter']], ['class Bla:'])
    typeAndCompare(['de', ['Space', '2'], ['Enter']], ['    def __init__(self):'])
    typeAndCompare(['pas', ['Meta', 'Enter']], ['        pass'])
    typeAndCompare(['def'])
    I.dontSee('def __init__', '.row-content')
    clear()
    
    typeAndCompare(['"".sta '], ['"".startswith()'])
    clear()

    typeAndCompare(['import logz', ['Meta', 'Enter'], 'log_format=""', ['Enter'], 'logz.LF('])
    typeAndCompare(['f'])
    typeAndCompare([' ='])
    typeAndCompare([' '], ['logzero.LogFormatter(fmt=log_format)'])
    clear()
    
    typeAndCompare(['fr bolt.g'])
    I.wait(1.5)
    typeAndCompare([' '], ['from boltons.gcutils '])
    clear()
    
    typeAndCompare(['1==2'], ['1 == 2'])
    clear()
    
    typeAndCompare(['def somet', ['Tab']], ['def something()'])
    typeAndCompare(['adog', ['Tab']], ['def something(a_dog)'])
    clear()
    
    typeAndCompare(['adog', ['Tab']], ['a_dog ='])
    clear()
    
    typeAndCompare(['fr .ml', ['Tab'], '(', ['Enter'], 'li '], ['from .ml import (', 'load_iris'])
    I.dontSee('load_iris()')
    clear()
    
    typeAndCompare(['cl cacheadog'])
    I.see('CacheADog', 'em')
    typeAndCompare([['Tab'], ['Enter']], ['class CacheADog:'])
    clear()
    
    typeAndCompare(['__adog', ['Tab']], ['__a_dog ='])
    clear()
    
    // pause()
})
