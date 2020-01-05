import { Pos } from '../lib/UIUtils'
import { isStringOrComment } from '../lib/Utils'
import g from '../lib/Globals'

const matchingBackward = { ')': '(', ']': '[', '}': '{' }
const matchingForward = { '(': ')', '[': ']', '{': '}' }

/**
 * a(b, |) -> false
 * a(b|)   -> true
 * @param {object} cm 
 */
function needInsertCommaBeforeParameter(cm) {
    const cursor = cm.getCursor()
    return scanInSameLevelOfBraces(cm, cursor, (cm, char /*, pos*/ ) => {
        if (/\s/.test(char)) {
            // return undefined
        } else if (/\(|,/.test(char)) {
            return false
        } else {
            return true
        }
    })
}

/**
 * a(|b)   -> true
 * a(b, |) -> false
 * @param {object} cm 
 */
function needInsertCommaAfterParameter(cm) {
    const cursor = cm.getCursor()
    return scanInSameLevelOfBraces(cm, cursor, (cm, char /*, pos*/ ) => {
        if (/\s/.test(char)) {
            // return undefined
        } else if (/\)|,/.test(char)) {
            return false
        } else {
            return true
        }
    }, 1) // scan forward
}

function isMultilineParameter(cm) {
    const cursor = cm.getCursor()
    const line = cursor.line
    const backwardScan = scanInSameLevelOfBraces(cm, cursor, (cm, char, pos) => {
        if (line !== pos.line) {
            return true
        } else if (/\(/.test(char)) {
            return false
        }
    })
    if (backwardScan) return true
    return scanInSameLevelOfBraces(cm, cursor, (cm, char, pos) => {
        if (line !== pos.line) {
            return true
        } else if (/\)/.test(char)) {
            return false
        }
    }, 1)
}

/**
 * Scan in braces
 * @param   {object}    cm       CodeMirror instance
 * @param   {object}    cursor   {line, ch}
 * @param   {function}  callback (cm, char, pos) => {false|string} to run for every character
 * @param   {direction} number   1 for forward; -1 for backward
 * @returns {object}    returns what the callback returns, or false
 */
function scanInSameLevelOfBraces(cm, cursor, callback, direction = -1) {
    console.assert(direction === 1 || direction === -1)
    const forward = (direction === 1)
    const matchingHalves = forward ? matchingForward : matchingBackward
    const stack = []
    const pos = Pos(0, 0)
    const endLine = forward ?
        Math.min(cm.lineCount(), cursor.line + 10) :
        Math.max(-1, cursor.line - 10)
    let stackTop
    for (let line = cursor.line; line !== endLine; line += direction) {
        const lineContent = cm.getLine(line)
        pos.line = line
        if (!lineContent) continue
        let ch = forward ? -1 : lineContent.length,
            end = forward ? lineContent.length : -1
        if (line === cursor.line) {
            ch = cursor.ch - direction
            if (!forward) ch -= 1
        }

        for (;;) {
            ch += direction
            if (forward) {
                if (ch >= end) break
            } else {
                if (ch <= end) break
            }
            pos.ch = ch
            const char = lineContent.charAt(ch)
            const anotherHalf = matchingHalves[char]
            if (anotherHalf) {
                if (isStringOrComment(cm, pos)) {
                    const token = cm.getTokenAt(pos)
                    ch = forward ? token.end : token.start
                    continue
                }
                stack.push(anotherHalf)
                stackTop = anotherHalf
                continue
            }
            if (char === stackTop) {
                if (isStringOrComment(cm, pos)) {
                    const token = cm.getTokenAt(pos)
                    ch = forward ? token.end : token.start
                    continue
                }
                stack.pop()
                stackTop = stack[stack.length - 1]
                continue
            }
            if (stack.length === 0) {
                const result = callback(cm, char, pos)
                if (result !== undefined) return result
            }
        }
    }
    return false
}

/**
 * some_function(aa|a) --> some_function(aaa|)
 * some_function(aa|a=123) --> some_function(aaa=123|)
 * some_function(aaa=12|3) --> some_function(aaa=123|)
 * @param {object} cm CodeMirror
 */
function moveCursorToParameterInsertionPoint(cm) {
    const cursor = cm.getCursor()
    const lineContent = cm.getLine(cursor.line).substring(0, cursor.ch)

    if (/,\s*$/.test(lineContent))
        return // it is already on the current position

    const newCursorPos = scanInSameLevelOfBraces(cm, cursor, (cm, char, pos) => {
        if (/,/.test(char)) {
            pos.ch += 1
            return pos
        }
        if (/\)/.test(char)) {
            return pos
        }
    }, 1)
    newCursorPos && cm.setCursor(newCursorPos)
}

function moveCursorToParameter(cm, target) {
    const cursor = cm.getCursor()
    let parameterPos = scanInSameLevelOfBraces(cm, cursor, (cm, char, pos) => {
        const token = cm.getTokenAt(pos)
        if (token.string === target) {
            return pos
        }
        if (pos.ch < token.end)
            pos.ch = token.end
    }, 1)

    if (!parameterPos)
        parameterPos = scanInSameLevelOfBraces(cm, cursor, (cm, char, pos) => {
            const token = cm.getTokenAt(pos)
            if (token.string === target) {
                return pos
            }
            if (pos.ch > token.start)
                pos.ch = token.start
        })


    if (!parameterPos) return false

    const startPos = scanInSameLevelOfBraces(cm, parameterPos, (cm, char, pos) => {
        const token = cm.getTokenAt(pos)
        if (/=/.test(char)) {
            pos.ch += 1
            return pos
        }
        if (pos.ch < token.end)
            pos.ch = token.end
    }, 1)
    const endPos = scanInSameLevelOfBraces(cm, parameterPos, (cm, char, pos) => {
        const token = cm.getTokenAt(pos)
        if (/\)|,/.test(char)) {
            return pos
        }
        if (pos.ch < token.end)
            pos.ch = token.end
    }, 1)
    cm.setSelection(startPos, endPos)
    return true
}

function setCursorAndScrollIntoView(line, ch) {
    const editor = g.activeEditor
    if (!editor) return
    const { cm } = editor
    const pos = Pos(line, ch)
    cm.setCursor(pos)
    cm.focus()
    const margin = editor.codeEditor.getBoundingClientRect().height * .2
    cm.scrollIntoView(pos, margin)
    return cm
}

export {
    needInsertCommaAfterParameter,
    needInsertCommaBeforeParameter,
    scanInSameLevelOfBraces,
    isMultilineParameter,
    matchingBackward,
    matchingForward,
    moveCursorToParameterInsertionPoint,
    moveCursorToParameter,
    setCursorAndScrollIntoView,
}
