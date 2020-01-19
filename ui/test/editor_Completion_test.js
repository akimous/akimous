Feature('Completion')

Scenario('Without realtime formatting', async (I) => {
    I.amOnPage('http://localhost:3178')
    I.waitForFrames(10)
    I.click('pre.CodeMirror-line')
    I.disableRealtimeFormatter()
        
    I.typeAndCompare(['for i in range(5):', 'Enter', 'print(i'],
        ['for i in range(5):', 'print(i)'])
    I.dontSee('pprint')
    I.clear()
    
    I.typeAndCompare(['for i in ra', 'Escape'])
    I.typeAndCompare(['ng '], ['range()'])
    I.clear()
    
    I.typeAndCompare(['fr s'], ['from'])
    I.waitForCompletionOrContinueIn(5)
    I.typeAndCompare(['ph'])
    I.typeAndCompare(['.'], ['from sphinx.'])
    I.typeAndCompare(['io im '], ['from sphinx.io import '])
    I.typeAndCompare(['rea', 'Enter'], ['from sphinx.io import read_doc'])
    I.clear()
    
    I.typeAndCompare(['"""classbla', ['Meta', 'Enter'], 'cla'])
    I.dontSee('classbla', '.row-content')
    I.clear()
    
    I.typeAndCompare(['cla C:', 'Enter'], ['class C:']) // single character class
    I.clear()
    
    I.typeAndCompare(['cla Bla:', 'Enter'], ['class Bla:'])
    I.typeAndCompare(['de', ['Space', '2'], ':', 'Enter'], ['    def __init__(self):'])
    I.typeAndCompare(['se.cat=1', 'Enter', 'pr se.c)', 'Enter'], ['self.cat=1', 'print(self.cat)'])
    I.typeAndCompare(['pas', ['Meta', 'Enter']], ['        pass'])
    I.typeAndCompare(['def'])
    I.dontSee('def __init__', '.row-content')
    I.clear()
    
    I.typeAndCompare(['"".sta '], ['"".startswith()'])
    I.clear()
    
    I.typeAndCompare(['import l'])
    I.waitForCompletionOrContinueIn(5)
    I.typeAndCompare(['ogz', ['Meta', 'Enter'], 'log_format=""', 'Enter', 'logz.LF('])
    I.typeAndCompare(['f', 'Tab'])
    I.typeAndCompare(['lf '], ['logzero.LogFormatter(fmt=log_format)'])
    I.clear()
    
    I.typeAndCompare(['fr bolt'])
    I.waitForCompletionOrContinueIn(5)
    I.typeAndCompare(['.g'])
    I.waitForCompletionOrContinueIn(5)
    I.typeAndCompare([' '], ['from boltons.gcutils '])
    I.clear()
    
    I.typeAndCompare(['1==2'], ['1==2'])
    I.clear()
    
    I.typeAndCompare(['def somet', 'Tab'], ['def something()'])
    I.typeAndCompare(['adog', 'Tab'], ['def something(a_dog)'])
    I.clear()
    
    I.typeAndCompare(['adog', 'Tab'], ['a_dog ='])
    I.clear()
    
    I.typeAndCompare(['fr .ml', 'Tab', '(', 'Enter', 'li '], 
        ['from .ml import (', 'load_iris'])
    I.dontSee('load_iris()')
    I.clear()
    
    I.typeAndCompare(['cl cacheadog'])
    I.see('CacheADog', 'em')
    I.typeAndCompare(['Tab', ':', 'Enter'], ['class CacheADog:'])
    I.clear()
    
    I.typeAndCompare(['__adog', 'Tab'], ['__a_dog ='])
    I.clear()
    
    I.typeAndCompare(['cla C:', 'Enter', '@pr', 'Enter', 'de adog', 'Tab'], 
        ['class C:', '    @property', '    def a_dog(self)'])
    I.clear()
    
    I.typeAndCompare(['"%s.'])
    I.see('Tab to commit the selected item')
    I.clear()
    
    I.typeAndCompare(['try:', 'Enter', 'pa', 'Enter', 'ex OS:', 'Enter'],
        ['try:', '    pass', 'except OSError:'])
    I.clear()
    
    I.typeAndCompare(['cachedir=[]', 'Enter', 'ifn any (term in ca )for te'],
        ['if not any((term in cachedir)for te)'])
    I.see('Tab to commit the selected item')
    I.clear()
    
    I.typeAndCompare(['pri "",flu', 'Tab', 'Tru '], ['print("",flush=True)'])
    I.clear()
    
    I.setDoc('class C:\n    def __init__(self):\n        pass\n\n    def cat(self):\n' + 
        '        pass\n\n')
    I.typeAndCompare([['Space', 'p'], 'Tab', 'd'])
    I.see('def', '.row-content')
    I.dontSee('def __init__', '.row-content')
    I.clear()
    
    // cursor should be inside of braces if completion has parameters
    I.typeAndCompare(['"".sp ".'], ['"".split(".")'])
    I.clear()
    
    // outside if not
    I.typeAndCompare(['"".ti +'], ['"".title()+'])
    I.clear()
    
    I.typeAndCompare(['(1,2).c '], ['(1,2).count()']) // should not be `(1, 2) .`
    I.clear()
    
    // forward delete
    I.typeAndCompare(['1', 'Enter', 'Enter', '23', ['ArrowUp'], ['Delete']], ['1\n23'])
    I.clear()
    
    // should not add tail for strings and comments
    I.typeAndCompare(['# demo', 'Tab'])
    I.dontSee('demo =')
    I.clear()
    
    // single character variable should still be completed
    I.typeAndCompare(['for k,v in {}.i :', 'Enter', 'v.'],
        ['for k,v in {}.items():', 'v.'])
    I.clear()
    
    // should not become `int(context )`
    I.typeAndCompare(['def t(context=1):', 'Enter', 'int(con '], ['int(context)'])
    I.clear()
    
    I.typeAndCompare(['a=[]', 'Enter', 'a[1:2+3'], ['a[1:2+3]'])
    I.clear()
    
    // make sure "in" is completed
    I.typeAndCompare(['if "" in ['], ['if "" in []'])
    I.clear()
    // pause()
})
