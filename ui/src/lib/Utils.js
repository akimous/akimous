import CodeMirror from 'codemirror'
import g from './Globals'
import { setProjectState } from './ConfigManager'

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

const queue = []
let lastFrameTimestamp = 0 // in ms
let framesPassed = 0
let ticking = false

function schedule(callback) {
    queue.push(callback)
    if (!ticking) {
        ticking = true
        requestAnimationFrame(tick)
    }
}

function tick(time) {
    const frameTime = time - lastFrameTimestamp
    lastFrameTimestamp = time
    framesPassed += 1
    // console.log({ frameTime, framesPassed })
    if (frameTime > 20 && framesPassed < 10) {
        requestAnimationFrame(tick)
        return
    }

    framesPassed = 0

    let job = queue.shift()
    while (job) {
        job()
        // console.log('job took', performance.now() - time, job)
        if (performance.now() - time > 4) break
        // consume next job
        job = queue.shift()
    }

    // if the queue is not empty, schedule next run
    if (queue.length === 0)
        ticking = false
    else requestAnimationFrame(tick)
}

function nextFrame(callback) {
    requestAnimationFrame(() => {
        requestAnimationFrame(callback)
    })
}

function initializeTabView(view, tabBar, title, icon) {
//    view.self = view
//    view.children = {}
    schedule(() => {
//        view.parent = view.parent
        view.tab = tabBar.openTab(view, title, icon, false)
//        view.tab.labeled = false
//        view.on('state', ({ changed, current }) => {
//            if (changed.active) {
//                view.tab.set({
//                    active: current.active
//                })
//            }
//        })
    })
}

function setAttributeForMultipleComponent(obj, ...targets) {
    for (const i of targets)
        i.set(obj)
}

//function activateView(parent, view) {
//    const oldView = parent.get().focus
//    if (view === oldView) return
//    parent.set({ focus: view })
//    if (!view) return
//    if (g.focusStack.includes(parent))
//        g.setFocus([parent, view])
//    oldView && oldView.set({ active: false })
//    view.set({ active: true })

//    let panel
//    if (parent === g.panelLeft) panel = 'left'
//    else if (parent === g.panelRight) panel = 'right'
//    if (panel)
//        setProjectState('activePanels', {
//            [panel]: view.name
//        })
//}

function reformatDocstring(doc) {
    if (!doc) return doc
    const lines = doc.split(/\r?\n/).map(line => line.trim())
    const maxLineLength = lines.reduce((accumulator, line) => {
        return Math.max(accumulator, line.length)
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

const Pos = CodeMirror.Pos

function isStringOrComment(cm, pos) {
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
                if (isStringOrComment(cm, pos)) {
                    const token = cm.getTokenAt(pos)
                    ch = token.start
                    pos.ch = ch
                    continue
                }
                braceStackCounter += 1
            } else if (char === close) {
                pos.ch = ch
                if (isStringOrComment(cm, pos)) {
                    const token = cm.getTokenAt(pos)
                    ch = token.start
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

/**
 * Emphasize input in target for completion display.
 * @param   {string} target e.g. "something"
 * @param   {string} input  e.g. "some"
 * @returns {string} e.g. "<em>some</em>thing"
 */
function highlightSequentially(target, input) {
    const result = []
    let t = 0
    let i = 0
    const tLength = target.length
    const iLength = input.length
    let iChar = input.charAt(i)

    for (; t < tLength; t++) {
        const tChar = target.charAt(t)
        if (tChar === iChar) {
            result.push(`<em>${tChar}</em>`)
            i += 1
            if (i >= iLength) {
                result.push(target.substring(t + 1))
                break
            }
            iChar = input.charAt(i)
        } else {
            result.push(tChar)
        }
    }
    return result.join('').replace(/<\/em><em>/g, '')
}

function joinPath(x) {
    if (x[0] === g.pathSeparator)
        return g.pathSeparator + x.slice(1).join(g.pathSeparator)
    return x.join(g.pathSeparator)
}

function capitalize(s) {
    return s && s.charAt(0).toUpperCase() + s.slice(1)
}

function highlightMatch(text, from, to) {
    const head = text.substring(0, from)
    const body = text.substring(from, to)
    const tail = text.substring(to)
    return `${head}<em>${body}</em>${tail}`
}

export {
    binarySearch,
    schedule,
    nextFrame,
    initializeTabView,
    setAttributeForMultipleComponent,
//    activateView,
    reformatDocstring,
    getRem,
    Pos,
    isStringOrComment,
    inSomething,
    inParentheses,
    inBrackets,
    inBraces,
    highlightSequentially,
    joinPath,
    capitalize,
    highlightMatch,
}
