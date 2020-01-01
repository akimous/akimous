import isEqual from 'lodash.isequal'

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
    let pos = {
        line: 0,
        ch: 0,
    }
    for (; line >= 0 && line > cursor.line - searchNLines; line--) {
        pos.line = line
        for (let ch = startCh - 1; ch > -1; ch--) {
            let char = lineContent.charAt(ch)
            if (char === open) {
                pos.ch = ch + 1
                if (isStringOrComment(cm, pos)) {
                    const token = cm.getTokenAt(pos)
                    ch = token.start
                    pos.ch = ch
                    continue
                }
                braceStackCounter += 1
            } else if (char === close) {
                pos.ch = ch + 1
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
        if (!lineContent) continue
        startCh = lineContent.length
    }
    return false
}

function inParentheses(cm, cursor) {
    return inSomething(cm, cursor, '(', ')')
}

//function inBrackets(cm, cursor) {
//    return inSomething(cm, cursor, '[', ']')
//}
//
//function inBraces(cm, cursor) {
//    return inSomething(cm, cursor, '{', '}')
//}

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
    const inputLowered = input.toLowerCase()
    let iChar = inputLowered.charAt(i)

    for (; t < tLength; t++) {
        const tChar = target.charAt(t)
        if (tChar.toLowerCase() === iChar) {
            result.push(`<em>${tChar}</em>`)
            i += 1
            if (i >= iLength) {
                result.push(target.substring(t + 1))
                break
            }
            iChar = inputLowered.charAt(i)
        } else {
            result.push(tChar)
        }
    }
    return result.join('').replace(/<\/em><em>/g, '')
}

/**
 * Highlight all occurrences of keywords in target.
 * @param   {string} target   e.g. 'abac'
 * @param   {Array}  keywords e.g. ['a', 'c']
 * @returns {string} highlighted string e.g. '<em>a</em>b<em>ac</em>'
 */
function highlightAllOccurrences(target, keywords) {
    const x = new Array(target.length).fill(0) // 1 if highlighted, 0 if not
    const targetLowered = target.toLowerCase()
    for (const keyword of keywords) {
        const keywordLowered = keyword.toLowerCase()
        const { length } = keywordLowered
        let start = 0
        let index
        while ((index = targetLowered.indexOf(keywordLowered, start)) > -1) {
            for (let i = 0; i < length; i++) {
                x[index + i] = 1
            }
            start = index + length
        }
    }
    const result = []
    for (let i = 0; i < target.length; i++) {
        if (x[i] && !x[i - 1]) {
            result.push('<em>')
        } else if (!x[i] && x[i - 1]) {
            result.push('</em>')
        }
        result.push(target.charAt(i))
    }
    if (x[x.length - 1]) {
        result.push('</em>')
    }
    return result.join('')
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

class CircularBuffer {
    constructor(size) {
        this.size = size
        this.buffer = new Array(size)
        this.index = 0
    }
    
    push(item) {
        const lastItem = this.buffer[this.index]
        if (isEqual(lastItem, item))
            return
        this.index = (this.index + 1) % this.size
        this.buffer[this.index] = item
    }
    
    remove(item) {
        for (let i = 0; i < this.size; i++) {
            if (isEqual(this.buffer[i], item))
                this.buffer[i] = null
        }
    }
    
    *iterate() {
        for (let i = 0; i < this.size; i++) {
            const index = (this.index - i) % this.size
            const item = this.buffer[index]
            if (!item) continue
            this.buffer[index] = null
            yield item
        }
    }
}

export {
    binarySearch,
    schedule,
    nextFrame,
    reformatDocstring,
    getRem,
    isStringOrComment,
    inSomething,
    inParentheses,
    // inBrackets,
    // inBraces,
    highlightSequentially,
    capitalize,
    highlightMatch,
    CircularBuffer,
    highlightAllOccurrences,
}
