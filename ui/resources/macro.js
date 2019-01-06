/**
 * Generate a macro callback function that can be used for print/log/... etc.
 * @param   {function} f (event, macroFormat, target) => string
 * @returns {function} a function that can be called in executeMacro(macro)
 */
function printerFactory(f) {
    return (cm, event, macroPanel) => {
        let target
        let cursor = cm.getCursor()

        // get target variable/statement to be printed
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

        const lineContent = cm.getLine(cursor.line)
        const isEmptyLine = /^\s*$/.test(lineContent)
        const { macroFormat } = macroPanel.get()
        const insertion = f(event, macroFormat, target)

        cm.operation(() => {
            cm.execCommand('goLineEnd')
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
        hotkey: 'i',
        name: 'logger.info',
        description: '',
        callback: printerFactory((event, macroFormat, target) => {
            if (event.shiftKey) {
                return `logger.info('${macroFormat.replace(/\${NAME}/g, target)} %r', ${target})`
            } else {
                return `logger.info(${target})`
            }
        })
    }, {
        hotkey: 'p',
        name: 'print',
        description: 'Insert print statement for the object under cursor.',
        callback: printerFactory((event, macroFormat, target) => {
            if (event.shiftKey) {
                return `print('${macroFormat.replace(/\${NAME}/g, target)}', ${target})`
            } else {
                return `print(${target})`
            }
        })
    }
]
