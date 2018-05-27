// https://stackoverflow.com/questions/22697936/binary-search-in-javascript
function binarySearch(array, target) {
    let lo = -1,
        hi = array.length
    while (1 + lo !== hi) {
        const mi = lo + ((hi - lo) >> 1)
        if (array[mi].name >= target) hi = mi
        else lo = mi
    }
    return hi
}

function onIdle(callback, timeout = 7000, delay = 1) {
    setTimeout(() => { // let other things run first
        if (window.requestIdleCallback) {
            window.requestIdleCallback(() => {
                requestAnimationFrame(callback)
            }, {
                timeout
            })
        } else {
            requestAnimationFrame(() => {
                console.warn('requestIdleCallback not available')
                requestAnimationFrame(callback)
            })
        }
    }, delay)
}

function initializeTabView(view, title, icon) {
    view.set({
        self: view,
    })
    view.children = {}
    setTimeout(() => {
        view.parent = view.get().parent
        view.tab = view.parent.tabBar.openTab(view, title, icon)
        view.tab.set({
            labeled: false
        })
        view.on('state', ({ changed, current }) => {
            if (changed.active) {
                view.tab.set({
                    active: current.active
                })
            }
        })
    })
}

function setAttributeForMultipleComponent(obj, ...targets) {
    for (const i of targets)
        i.set(obj)
}

function activateView(parent, view) {
    const oldView = parent.get().focus
    if (view === oldView) return
    parent.set({
        focus: view
    })
    if (!view) return
    oldView && oldView.set({
        active: false
    })
    view.set({
        active: true
    })
}

function reformatDocstring(doc) {
    if (!doc) return doc
    const lines = doc.split(/\r?\n/).map(line => line.trim())
    const maxLineLength = lines.reduce((accumlator, line) => {
        return Math.max(accumlator, line.length)
    }, 0) - 1

    const result = []
    const temp = []
    const insertLine = line => {
        if (temp.length) {
            if (line.startsWith('>>>')) {
                result.push(temp.join(' '))
                result.push(line)
                console.warn('start with >>>')
            }
            temp.push(line)
            result.push(temp.join(' '))
            temp.length = 0
        } else {
            result.push(line)
        }
    }
    for (let i = 0; i < lines.length - 1; i++) {
        const line = lines[i]
        const currentLineLength = line.length

        // current line is short, almost for sure it is not wrapped
        if (currentLineLength < maxLineLength * .7) {
            insertLine(line)
            continue
        }
        const nextLine = lines[i + 1].trim()
        let nextWordLength = nextLine.indexOf(' ')
        if (nextWordLength < 0) nextWordLength = nextLine.length

        // current line is wrapped
        if (currentLineLength + nextWordLength >= maxLineLength) {
            if (nextLine.startsWith('>>>')) {
                insertLine(line)
            } else
                temp.push(line)
            continue
        }
        // current line is not wrapped
        insertLine(line)
    }
    if (lines.length > 0) { // process last line
        insertLine(lines[lines.length - 1])
    }
    return result.join('\n')
}

function getRem() {
    return parseFloat(getComputedStyle(document.documentElement).fontSize)
}

function Pos(line, ch) {
    return { line, ch }
}

function shouldIgnoreToken(cm, pos) {
    const type = cm.getTokenTypeAt(pos)
    return type === 'string' || type === 'comment'
}

function inSomething(cm, cursor, open, close) {
    const searchNLines = 20
    let line = cursor.line
    let lineContent = cm.doc.getLine(line)

    let braceStackCounter = 0
    let startCh = cursor.ch
    let pos = Pos(0, 0)
    for (; line >= 0 && line > cursor.line - searchNLines; line--) {
        pos.line = line
        for (let ch = startCh - 1; ch > -1; ch--) {
            let char = lineContent.charAt(ch)
            if (char === open) {
                pos.ch = ch
                if (shouldIgnoreToken(cm, pos)) {
                    const token = cm.getTokenAt(pos)
                    ch = token.start - 1
                    pos.ch = ch
                    continue
                }
                braceStackCounter += 1
            } else if (char === close) {
                pos.ch = ch
                if (shouldIgnoreToken(cm, pos)) {
                    const token = cm.getTokenAt(pos)
                    ch = token.start - 1
                    pos.ch = ch
                    continue
                }
                braceStackCounter -= 1
            }
            if (braceStackCounter > 0) {
                return pos
            }
        }
        // if it is already top level statement, stop searching
        if (lineContent.charAt(0) !== ' ') {
            return false
        }
        lineContent = cm.doc.getLine(line - 1)
        startCh = lineContent.length
    }
    return false
}

function inParentheses(cm, cursor) {
    return inSomething(cm, cursor, '(', ')')
}

function inBrackets(cm, cursor) {
    return inSomething(cm, cursor, '[', ']')
}

function inBraces(cm, cursor) {
    return inSomething(cm, cursor, '{', '}')
}

export {
    binarySearch,
    onIdle,
    initializeTabView,
    setAttributeForMultipleComponent,
    activateView,
    reformatDocstring,
    getRem,
    inSomething,
    inParentheses,
    inBrackets,
    inBraces,
}
