import { Pos, isStringOrComment } from '../lib/Utils'

const matchingBackward = { ')': '(', ']': '[', '}': '{' }

/**
 * a(b, |) -> false
 * a(b)    -> true
 * @param {object} cm 
 */
function needInsertCommaBeforeParameter(cm) {
    const cursor = cm.getCursor()
    return scanInSameLevelOfBraces(cm, cursor, (cm, char/*, pos*/) => {
        if (/\s/.test(char)) {
            // return undefined
        } else if (/\(|,/.test(char)) {
            return false
        } else {
            return true
        }
    })
}

function isMultilineParameter(cm) {
    const cursor = cm.getCursor()
    let line = null
    return scanInSameLevelOfBraces(cm, cursor, (cm, char, pos) => {
        if (line === null) {
            line = pos.line
            return undefined
        } else if (line !== pos.line) {
            return true
        } else if (/\(|,/.test(char)) {
            return false
        }
    })
}

/**
 * Backward scan in braces
 * @param   {object}   cm       CodeMirror instance
 * @param   {object}   cursor   {line, ch}
 * @param   {function} callback (cm, char, pos) => {false|string} to run for every character
 * @returns {object}   returns what the callback returns, or false
 */
function scanInSameLevelOfBraces(cm, cursor, callback) {
    const stack = []
    let stackTop
    const pos = Pos(0, 0)
    for (let line = cursor.line; line >= Math.max(0, cursor.line - 10); line--) {
        const lineContent = cm.getLine(line)
        pos.line = line
        if (!lineContent) continue
        let ch = lineContent.length - 1,
            end = -1
        if (line === cursor.line) ch = cursor.ch - 1

        for (; ch > end; ch--) {
            pos.ch = ch
            const char = lineContent.charAt(ch)
            const opening = matchingBackward[char]
            if (opening) {
                if (isStringOrComment(cm, pos)) {
                    const token = cm.getTokenAt(pos)
                    ch = token.start
                    continue
                }
                stack.push(opening)
                stackTop = opening
                continue
            }
            if (char === stackTop) {
                if (isStringOrComment(cm, pos)) {
                    const token = cm.getTokenAt(pos)
                    ch = token.start
                    continue
                }
                stackTop = stack.pop()
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

export {
    needInsertCommaBeforeParameter,
    scanInSameLevelOfBraces,
    isMultilineParameter
}
