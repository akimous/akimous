import { inParentheses, inBrackets, inBraces } from '../lib/Utils'

const RealtimeFormatter = (editor, CodeMirror) => {
    let cm, c
    const Pos = CodeMirror.Pos

    const operators = /((\/\/=|>>=|<<=|\*\*=)|([+\-*/%&|^@!<>=]=)|(<>|<<|>>|\/\/|\*\*|->)|[+\-*/%&|^~<>!@=])$/
    const compoundOperators = /((\/\/=|>>=|<<=|\*\*=)|([+\-*/%&|^@!<>=]=)|(<>|<<|>>|\/\/|\*\*|->))$/
    const operatorChars = /[=+\-*/|&^~%@><!]$/
    const idendifier = /^[^\d\W]\w*$/
    const _inParentheses = () => inParentheses(cm, c.from)
    const _inBrackets = () => inBrackets(cm, c.from)
    const _inBraces = () => inBraces(cm, c.from)

    const ensureSpaceBefore = (t0) => {
        if (/\s+/.test(t0.string)) return // don't duplicate spaces
        c.text[0] = ' ' + c.text[0]
        editor.predictor.firstTriggeredCharPos.ch++
    }
    const stripTrailingSpaces = (line) => {
        for (let i = c.from.ch - 1; i >= 0; i--) {
            if (line.charAt(i) !== ' ') {
                c.update(Pos(c.from.line, i + 1), c.from, '')
                return
            }
        }
    }

    const inputHandler = (line, t0, t1, t2, isInFunctionSignatureDefinition) => {
        // skip if there are no characters before cursor 
        if (c.to.ch === 0) return

        const leftText = t0.string
        const lastChar = leftText.slice(-1)
        const currentText = c.text[0]
        const currentState = cm.getTokenAt(c.from).state
        if (currentState.scopes === undefined) return
        const currentScope = currentState.scopes[currentState.scopes.length - 1]

        const existSpaceBeforePreviousToken = /\s$/.test(t1.string)
        const leftTextIsOperator = operators.test(leftText)
        const currentTextIsPartOfTheOperator = compoundOperators.test(leftText + currentText)
        const currentTextIsOperator = operatorChars.test(currentText)
        if (editor.debug) console.log({
            currentTextIsPartOfTheOperator,
            currentTextIsOperator,
            leftTextIsOperator,
            existSpaceBeforePreviousToken,
            currentText,
            leftText,
            t2,
            t1,
            t0,
            'll': leftText + lastChar,
            'state': currentState,
            'scope': currentScope,
            'lineContent': cm.doc.getLine(c.from.line)
        })

        // skip if the cursor is in a string
        if (t0.type === 'comment' || (t0.type === 'string' && !(t0.end === c.to.ch))) return
        if (currentText === '') { // new line
            stripTrailingSpaces(line)
            line = cm.doc.getLine(c.from.line)
            const inScope = _inParentheses() || _inBrackets() || _inBraces()
            let tr = ''
            if (inScope) {
                try {
                    tr = cm.doc.getRange(Pos(inScope.line, inScope.ch + 1),
                        Pos(inScope.line, inScope.ch + 2))
                } catch (e) {
                    // skip this test if out of range
                }
                const shouldAlignOpenParenthesis = tr && !/\s/.test(tr) && !/\)/.test(tr)
                editor.cmEventDispatcher.setIndentAfterChange(
                    shouldAlignOpenParenthesis ? currentScope.align : currentScope.offset + 4
                )
            } else if ((/^\s*(if|def|for|while|with|class)\s.+[^\\:;]$/.test(line) ||
                    /^\s*(try|except|finally)/.test(line)
            ) && !/(:\s)|;$/.test(line) &&
                t0.string !== ':'
            ) { // add : if needed
                c.text[0] = c.text[0] + ':'
            } else if (c.from.ch === line.length && /[)}\]]$/.test(t0.string)) {
                const openBracket = cm.findMatchingBracket(c.from)
                const openBracketLine = cm.doc.getLine(openBracket.to.line)
                if ((/^\s*(if|def|for|while|with|class)\s/.test(openBracketLine) ||
                        /^\s*(try|except|finally)/.test(openBracketLine)
                ) && t0.string !== ':') {
                    c.text[0] = c.text[0] + ':'
                }
            } else if (currentState.lastToken === 'break') {
                editor.cmEventDispatcher.setIndentAfterChange(currentScope.offset - 4)
            }
        } else if (currentText[0] === ' ') {
            return
        } else if (currentText[0] === ',') {
            return
        } else if (t0.string === ',' && !/^[)}\]]/.test(currentText)) {
            c.text[0] = ' ' + c.text[0]
        } else if (t0.string === ':' && !_inBrackets()) {
            c.text[0] = ' ' + c.text[0]
        } else if (currentText === '=') {
            if (lastChar === '=' && leftText[leftText.length - 2] !== ' ') { // == case
                const pos = Pos(c.from.line, c.from.ch - 1)
                c.update(pos, pos, [' ='])
            } else if (currentTextIsPartOfTheOperator) { // +=, -=... etc
                return
            } else if (currentScope.type !== ')') { // not kwargs
                ensureSpaceBefore(t0)
            } else if (/\s+/.test(t1.string) && t2.string === ':') {
                ensureSpaceBefore(t0)
            }
        } else if (currentText === '#' && t0.type !== 'comment') {
            if (!/\s+/.test(t0.string))
                c.text[0] = ' ' + c.text[0]
        } else if (currentText === '+' && t0.string === '+') { // a++ => a += 1
            c.text[0] = '= 1'
        } else if (currentText === '-' && t0.string === '-') { // a-- => a-= 1
            c.text[0] = '= 1'
        } else if (currentTextIsOperator) {
            if (currentTextIsPartOfTheOperator) return
            if (/[(,]/.test(t0.string)) return
            if (_inBrackets()) return
            if (isInFunctionSignatureDefinition) return // def a(n=|-1) should not add space at |
            if (t0.string === 'e' && /[0-9]$/.test(t1.string)) return
            ensureSpaceBefore(t0)
        } else if (leftTextIsOperator && existSpaceBeforePreviousToken) {
            if (/[(,]/.test(t1.string)) return // (**|kwargs) => t1=='('
            if (/\s+/.test(t1.string) && /[(,]/.test(t2.string)) return // (a, *|args) => t2==','
            if (/[+-]/.test(t0.string) && /\s+/.test(t1.string) && !/[\])]/.test(t2.string) &&
                (t2.type !== 'variable') && (t2.type !== 'string') && (t2.type !== 'number') // a = -3
            ) return
            ensureSpaceBefore(t0)
        } else if (t0.string === '=' && t2.string === ' ' && /[!><=@]/.test(t1.string)) { // special case for a = b ==|2
            ensureSpaceBefore(t0)
        } else if (t0.string === '#') {
            ensureSpaceBefore(t0)
        } else if (t0.string === '>' && t1.string === '-') {
            ensureSpaceBefore(t0)
        } else if (t0.string === '.' && t1.type === null && idendifier.test(currentText)) {
            // .x => self.x
            c.cancel()
            const from = Pos(c.from.line, c.from.ch - 1)
            cm.doc.replaceRange('self.' + currentText, from, c.to)
        } else {
            if (editor.debug) console.log('none of above applies')
        }
    }

    const deleteChars = (lines, chars) => {
        let replaceWith = ''
        const from = Pos(c.from.line - lines, c.to.ch - chars)
        const to = c.to
        if (lines > 0) {
            const lineContent = cm.doc.getLine(c.from.line - lines)
            from.ch = lineContent.length - chars
            if (/[,;:]$/.test(lineContent)) replaceWith = ' '
        }
        c.cancel() // must go before replaceRange
        cm.doc.replaceRange(replaceWith, from, to)
    }

    const forwardDeleteChars = (lines, chars) => {
        let replaceWith = ''
        const from = Pos(c.from.line, c.from.ch)
        const to = Pos(c.to.line, c.to.ch + chars - 1)
        if (lines > 0) {
            const lineContent = cm.doc.getLine(from.line)
            const nextLineContent = cm.doc.getLine(from.line + lines)
            if (/[,;:]$/.test(lineContent)) replaceWith = ' '
            const indent = nextLineContent.match(/^\s+/)
            if (indent)
                to.ch = indent[0].length
        }
        c.cancel() // must go before replaceRange
        cm.doc.replaceRange(replaceWith, from, to)
    }

    const deleteHandler = () => {
        const cursor = cm.doc.getCursor()
        if (c.from.ch === cursor.ch - 1) { // handle backspace
            const t0 = cm.getTokenAt(c.to, true)
            if (t0.type === 'string' || t0.type === 'comment') return
            const tx = cm.doc.getRange(Pos(c.from.line, c.from.ch - 4), c.to)
            if (/\s+/.test(t0.string) && t0.start === 0) { // start of line indentations
                deleteChars(1, 0)
            } else if (/\S[,:;]\s$/.test(tx)) {
                deleteChars(0, 2)
            } else if (/\S\s[=+\-*/|&^~%@><]\s$/.test(tx)) {
                deleteChars(0, 3)
            } else if (/\S[=<>/*]\s$/.test(tx)) {
                deleteChars(0, 2)
            } else if (/\s[=+\-*/|&^%@<>!]$/.test(tx)) {
                deleteChars(0, 2)
            }
        } else if (c.from.ch === cursor.ch) { // handle forward delete
            const tx = cm.doc.getRange(c.from, Pos(c.to.line, c.to.ch + 4))
            if (c.from.line === c.to.line - 1) {
                forwardDeleteChars(1, 0)
            } else if (/^[,:;]\s\S/.test(tx)) {
                forwardDeleteChars(0, 2)
            } else if (/^\s[=+\-*/|&^~%@><]\s\S/.test(tx)) {
                forwardDeleteChars(0, 3)
            } else if (/^\s[=+\-*/|&^%@<>!]\S/.test(tx)) {
                forwardDeleteChars(0, 2)
            } else if (/^[=<>/*]\s/.test(tx)) {
                forwardDeleteChars(0, 2)
            }
        }
    }

    return {
        debug: true,
        inputHandler,
        deleteHandler,
        setContext: (codemirror, changeObj) => {
            cm = codemirror
            c = changeObj
        },
    }
}

export default RealtimeFormatter
