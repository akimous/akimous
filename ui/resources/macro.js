function getNTokens(cm, n) {
    const tokens = Array(n)
    const pos = cm.getCursor()
    pos.ch += 1
    for (let i = 0; i < n; i++) {
        try {
            const token = cm.getTokenAt(pos, true)
            tokens[i] = token
            pos.ch = token.end + 1
        } catch (e) {
            console.error(e)
        }
    }
    return tokens
}

function getTargetVariableOrStatement(cm) {
    let target
    const cursor = cm.getCursor()
    if (cm.somethingSelected()) {
        target = cm.getSelection()
    } else {
        let token = cm.getTokenAt(cursor)
        if (token.type && token.string.length && token.type != 'punctuation') {
            target = token.string
        } else {
            cursor.ch += 1
            token = cm.getTokenAt(cursor)
            if (!(token.type && token.string.length && token.type != 'punctuation'))
                target = ''
            else
                target = token.string
        }
    }
    return target
}

/**
 * Generate a macro callback function that can be used for print/log/... etc.
 * @param   {function} f (event, macroFormatWithShift, target) => string
 * @returns {function} a function that can be called in executeMacro(macro)
 */
function printerFactory(f) {
    return (cm, event, macroPanel) => {
        let target = getTargetVariableOrStatement(cm)
        let cursor = cm.getCursor()

        const lineContent = cm.getLine(cursor.line)
        const isEmptyLine = /^\s*$/.test(lineContent)
        const { macroFormatWithShift } = macroPanel
        const insertion = f(event, macroFormatWithShift, target)

        cm.operation(() => {
            cm.setCursor(cursor.line, lineContent.length)
            if (target.length || !isEmptyLine)
                cm.execCommand('newlineAndIndent')
            cursor = cm.getCursor()
            cm.replaceRange(insertion, cursor, cursor)
            if (!target.length)
                cm.execCommand('goCharLeft')
        })
        cm.focus()
    }
}

export default [
    {
        hotkey: 'd',
        name: 'logger.debug',
        callback: printerFactory((event, macroFormatWithShift, target) => {
            if (event.shiftKey) {
                return `logger.debug('${macroFormatWithShift.replace(/\${NAME}/g, target)} %r', ${target})`
            } else {
                return `logger.debug(${target})`
            }
        })
    }, {
        hotkey: 'i',
        name: 'logger.info',
        callback: printerFactory((event, macroFormatWithShift, target) => {
            if (event.shiftKey) {
                return `logger.info('${macroFormatWithShift.replace(/\${NAME}/g, target)} %r', ${target})`
            } else {
                return `logger.info(${target})`
            }
        })
    }, {
        hotkey: 'w',
        name: 'logger.warning',
        callback: printerFactory((event, macroFormatWithShift, target) => {
            if (event.shiftKey) {
                return `logger.warning('${macroFormatWithShift.replace(/\${NAME}/g, target)} %r', ${target})`
            } else {
                return `logger.warning(${target})`
            }
        })
    }, {
        hotkey: 'e',
        name: 'logger.error',
        callback: printerFactory((event, macroFormatWithShift, target) => {
            if (event.shiftKey) {
                return `logger.error('${macroFormatWithShift.replace(/\${NAME}/g, target)} %r', ${target})`
            } else {
                return `logger.error(${target})`
            }
        })
    }, {
        hotkey: 'c',
        name: 'logger.critical',
        callback: printerFactory((event, macroFormatWithShift, target) => {
            if (event.shiftKey) {
                return `logger.critical('${macroFormatWithShift.replace(/\${NAME}/g, target)} %r', ${target})`
            } else {
                return `logger.critical(${target})`
            }
        })
    }, {
        hotkey: 'x',
        name: 'logger.exception',
        callback: printerFactory((event, macroFormatWithShift, target) => {
            if (event.shiftKey) {
                return `logger.exception('${macroFormatWithShift.replace(/\${NAME}/g, target)} %r', ${target})`
            } else {
                return `logger.exception(${target})`
            }
        })
    }, {
        hotkey: 'p',
        name: 'print',
        callback: printerFactory((event, macroFormatWithShift, target) => {
            if (event.shiftKey) {
                return `print('${macroFormatWithShift.replace(/\${NAME}/g, target)}', ${target})`
            } else {
                return `print(${target})`
            }
        })
    }, {
        hotkey: 'b',
        name: 'breakpoint',
        callback: printerFactory(() => {
            return 'breakpoint()'
        })
    }, {
        hotkey: 'r',
        name: 'return',
        callback: (cm) => {
            let target = getTargetVariableOrStatement(cm)
            cm.operation(() => {
                if (!cm.somethingSelected()) {
                    // check if it is an assignment statement
                    cm.execCommand('goLineEnd')
                    cm.execCommand('goLineStartSmart')
                    const [t0, , t2] = getNTokens(cm, 3)
                    if (t2.string === '=' && t0.type === 'variable') {
                        target = t0.string
                    } else if (target.length === 0 && t0.type === 'variable') {
                        target = t0.string
                    }
                }
                // insert return statement
                cm.execCommand('goLineEnd')
                const lineContent = cm.getLine(cursor.line)
                const isEmptyLine = /^\s*$/.test(lineContent)
                if (target.length || !isEmptyLine)
                    cm.execCommand('newlineAndIndent')
                const cursor = cm.getCursor()
                cm.replaceRange(`return ${target}`, cursor, cursor)
                if (!target.length)
                    cm.execCommand('goCharLeft')
            })
        }
    }, {
        hotkey: 't',
        name: 'try-except',
        callback: (cm) => {
            const fromLine = cm.getCursor('from').line
            const toLine = cm.getCursor('to').line
            cm.operation(() => {
                cm.setCursor(fromLine, 0)
                cm.execCommand('goLineEnd')
                cm.execCommand('goLineStartSmart')
                cm.execCommand('newlineAndIndent')
                cm.execCommand('goLineUp')
                let start = cm.getCursor()
                cm.replaceRange('try:', start, start)
                start = {
                    line: fromLine + 1,
                    ch: 0
                }
                const end = {
                    line: toLine + 2,
                    ch: 0
                }
                cm.setSelection(start, end)
                cm.execCommand('indentMore')
                end.line = toLine + 1
                cm.setCursor(end)
                cm.execCommand('goLineEnd')
                cm.execCommand('newlineAndIndent')
                cm.execCommand('indentLess')
                const cursor = cm.getCursor()
                cm.replaceRange('except ', cursor, cursor)
                cm.execCommand('goCharLeft')
            })
            cm.focus()
        }
    }
]
