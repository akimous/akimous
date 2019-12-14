const assert = require('assert')
Feature('Realtime Formatter')

const META = (process.platform === 'darwin') ? 'Meta' : 'Control'

Scenario('Normal formatting', async (I) => {
    await I.amOnPage('http://localhost:3178')
    await I.waitForFrames(7)
    await I.click('pre.CodeMirror-line')

    const specialKeys = new Set(['Enter', 'Space'])
    const typeAndCompare = async (inputs, displays) => {
        for (const i of inputs) {
            let first = true
            if (Array.isArray(i)) {
                I.type(i)
            } else if (specialKeys.has(i)) {
                I.pressKey(i)
            } else {
                for (const j of i) {
                    if (!/[0-9a-zA-Z]/.test(j)){
                        I.pressKey(j)
                        if (/[\s"(),[\]{}]/.test(j))
                            continue
                        I.waitForCompletionOrContinueIn(.5)
                    } else if (first) {
                        I.pressKey(j)
                        I.waitForCompletionOrContinueIn(.5)
                        first = false
                    } else {
                        I.pressKey(j)
                    }
                }
            }
        }
        if (!displays) return
        const doc = await I.getDoc()
        for (const i of displays) {
            assert(doc.includes(i), `Not found: ${i}\nActual:\n${doc}`)
        }
    }
    const paste = async (content) => {
        await I.executeScript(function(content) {
            window.g.activeEditor.cm.setValue(content)
        }, content)
    }
    const clear = () => {
        I.type(['Escape'])
        I.type([META, 'a'])
        I.type(['Backspace'])
    }
        
    await typeAndCompare(['for i in range(5', ['Meta', 'Enter'], 'print(i'],
        ['for i in range(5):', 'print(i)'])
    I.dontSee('pprint')
    clear()

    await typeAndCompare(['for i in ra', ['Escape']])
    await typeAndCompare(['ng '], ['range()'])
    clear()
    
    await typeAndCompare(['fr s'], ['from'])
    I.waitForCompletionOrContinueIn(3)
    await typeAndCompare(['ph'])
    await typeAndCompare(['.'], ['from sphinx.'])
    await typeAndCompare(['io im '], ['from sphinx.io import '])
    await typeAndCompare(['rea', ['Enter']], ['from sphinx.io import read_doc'])
    clear()
    
    await typeAndCompare(['"""classbla', ['Meta', 'Enter'], 'cla'])
    await I.dontSee('classbla', '.row-content')
    clear()
    
    await typeAndCompare(['cla C', ['Enter']], ['class C:']) // single character class
    clear()
    
    await typeAndCompare(['cla Bla', ['Enter']], ['class Bla:'])
    await typeAndCompare(['de', ['Space', '2'], ['Enter']], ['    def __init__(self):'])
    await typeAndCompare(['.cat=1', ['Enter'], 'pr .ca)', ['Enter']], ['self.cat = 1', 'print(self.cat)'])
    await typeAndCompare(['pas', ['Meta', 'Enter']], ['        pass'])
    await typeAndCompare(['def'])
    I.dontSee('def __init__', '.row-content')
    clear()
    
    await typeAndCompare(['"".sta '], ['"".startswith()'])
    clear()

    await typeAndCompare(['import l'])
    I.waitForCompletionOrContinueIn(3)
    await typeAndCompare(['ogz', ['Meta', 'Enter'], 'log_format=""', ['Enter'], 'logz.LF('])
    await typeAndCompare(['f', ['Tab']])
    await typeAndCompare(['lf '], ['logzero.LogFormatter(fmt=log_format)'])
    clear()
    
    await typeAndCompare(['fr bolt.g'])
    I.waitForCompletionOrContinueIn(3)
    await typeAndCompare([' '], ['from boltons.gcutils '])
    clear()
    
    await typeAndCompare(['1==2'], ['1 == 2'])
    clear()
    
    await typeAndCompare(['def somet', ['Tab']], ['def something()'])
    await typeAndCompare(['adog', ['Tab']], ['def something(a_dog)'])
    clear()
    
    await typeAndCompare(['adog', ['Tab']], ['a_dog ='])
    clear()
    
    await typeAndCompare(['fr .ml', ['Tab'], '(', ['Enter'], 'li '], 
        ['from .ml import (', 'load_iris'])
    I.dontSee('load_iris()')
    clear()
    
    await typeAndCompare(['cl cacheadog'])
    I.see('CacheADog', 'em')
    await typeAndCompare([['Tab'], ['Enter']], ['class CacheADog:'])
    clear()
    
    await typeAndCompare(['__adog', ['Tab']], ['__a_dog ='])
    clear()
    
    await typeAndCompare(['cla C', ['Enter'], '@pr', ['Enter'], 'de adog', ['Tab']], 
        ['class C:', '    @property', '    def a_dog(self)'])
    clear()
    
    await typeAndCompare(['"%s.'])
    I.see('Tab to commit the selected item')
    clear()
    
    await typeAndCompare(['try', ['Enter'], 'pa', ['Enter'], 'ex OS', ['Enter']],
        ['try:', '    pass', 'except OSError:'])
    clear()
    
    await typeAndCompare(['cachedir=[]', ['Enter'], 'ifn any (term in ca )for te'],
        ['if not any((term in cachedir) for te)'])
    I.see('Tab to commit the selected item')
    clear()
    
    await typeAndCompare(['pri "",flu', ['Tab'], 'Tru '], ['print("", flush=True)'])
    clear()
    
    await paste('class C:\n    def __init__(self):\n        pass\n\n    def cat(self):\n' + 
        '        pass\n\n')
    await typeAndCompare([['Space', 'p'], ['Tab'], 'd'])
    I.see('def', '.row-content')
    I.dontSee('def __init__', '.row-content')
    clear()
    
    // cursor should be inside of braces if completion has parameters
    await typeAndCompare(['"".sp ".'], ['"".split(".")'])
    clear()
    
    // outside if not
    await typeAndCompare(['"".ti +'], ['"".title() +'])
    clear()
    
    await typeAndCompare(['(1,2).c '], ['(1, 2).count()']) // should not be `(1, 2) .`
    clear()
    
    // forward delete
    await typeAndCompare(['1', ['Enter'], ['Enter'], '23', ['ArrowUp'], ['Delete']], ['1\n23'])
    clear()
    
    // should not add tail for strings and comments
    await typeAndCompare(['# demo', ['Tab']])
    I.dontSee('demo =')
    clear()
    
    // single character variable should still be completed
    await typeAndCompare(['for k,v in {}.i', ['Enter'], 'v.'],
        ['for k, v in {}.items():', 'v.'])
    clear()
    // pause()
})
