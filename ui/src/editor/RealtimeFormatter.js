import { inParentheses, inBrackets } from '../lib/Utils'
import { config } from '../lib/ConfigManager'

const RealtimeFormatter = (editor, CodeMirror) => {
    let cm, c
    const Pos = CodeMirror.Pos

    const operators = /((\/\/=|>>=|<<=|\*\*=)|([+\-*/%&|^@!<>=]=)|(<>|<<|>>|\/\/|\*\*|->)|[+\-*/%&|^~<>!@=])$/
    const compoundOperators = /((\/\/=|>>=|<<=|\*\*=)|([+\-*/%&|^@!<>=]=)|(<>|<<|>>|\/\/|\*\*|->))$/
    const operatorChars = /^[=+\-*/|&^~%@><!]$/
    const identifier = /^[^\d\W]\w*$/
    const fromImport = /^\s*(import|from)\s/
    const _inParentheses = () => inParentheses(cm, c.from)
    const _inBrackets = () => inBrackets(cm, c.from)

    const ensureSpaceBefore = (t0) => {
        if (/\s+/.test(t0.string)) return // don't duplicate spaces
        c.text[0] = ' ' + c.text[0]
        const pos = {...editor.completionProvider.firstTriggeredCharPos}
        pos.ch++
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
        if (!config.formatter.realtime) return
        // skip if there are no characters before cursor 
        if (c.to.ch === 0) return
        if (!c.text) return
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
        //console.log({
        //    currentTextIsPartOfTheOperator,
        //    currentTextIsOperator,
        //    leftTextIsOperator,
        //    existSpaceBeforePreviousToken,
        //    currentText,
        //    leftText,
        //    t2,
        //    t1,
        //    t0,
        //    'll': leftText + lastChar,
        //    'state': currentState,
        //    'scope': currentScope,
        //    'lineContent': cm.doc.getLine(c.from.line)
        //})

        // split string into two lines if enter is pressed inside a string token
        if (c.text.length === 2 && currentText === '' && t0.type === 'string' 
            && t0.start < c.from.ch && c.from.ch < t0.end) {
            let quote = t0.string[0]
            if (t0.string[1] === quote && t0.string[2] === quote)
                return // do nothing if is triple quote 
            c.text[0] = `${quote} \\`
            c.text[1] = quote
        }
        // skip if the cursor is in a string
        if (t0.type === 'comment' || (t0.type === 'string' && !(t0.end === c.to.ch))) return
        if (currentText === '') { // new line
            stripTrailingSpaces(line)
            const inParentheses = _inParentheses()
            if (inParentheses) {
                try {
                    if (t0.string === '(' && /^\s*def\s/.test(line)) {
                        // add extra indentation when inserting new line at, e.g.
                        // def something(|a, b)
                        editor.cmEventDispatcher.adjustIndent(1)
                    }
                } catch (e) {
                    // skip this test if out of range
                }
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
            } else if (t1.string === 'break') {
                editor.cmEventDispatcher.adjustIndent(-1)
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
            if (lastChar === '=' && !/\s+/.test(t1.string) && leftText[leftText.length - 2] !== ' ') { 
                // == case
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
        } else if (t0.string === '.' && t1.type === null && identifier.test(currentText)) {
            const lineContent = cm.doc.getLine(c.from.line)
            if (fromImport.test(lineContent)) return
            // .x => self.x
            c.text[0] = `self.${currentText}`
            c.from = Pos(c.from.line, c.from.ch - 1)
        } else {
            // console.debug('none of above applies')
        }
    }

    const deleteChars = (lines, chars) => {
        let replaceWith = ''
        const from = Pos(c.from.line - lines, c.to.ch - chars)
        if (lines > 0) {
            const lineContent = cm.doc.getLine(c.from.line - lines)
            from.ch = lineContent.length - chars
            if (/[,;:]$/.test(lineContent)) replaceWith = ' '
        }
        c.text[0] = replaceWith
        c.from = from
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
        c.text[0] = replaceWith
        c.from = from
        c.to = to
    }

    const deleteHandler = () => {
        if (!config.formatter.realtime) return
        if (cm.somethingSelected()) return
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
        } else if (c.from.ch < cursor.ch) {
            const t0 = cm.getTokenAt(c.to, true)
            if (/\s+/.test(t0.string) && t0.start === 0) { // start of line indentations
                deleteChars(1, 0)
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
