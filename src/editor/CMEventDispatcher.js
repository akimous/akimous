import g from '../lib/Globals'
import { CLOSED, TRIGGERED, RETRIGGERED } from './completion/CompletionProvider'

class CMEventDispatcher {
    constructor(editor) {
        const cm = editor.cm,
            doc = cm.doc,
            formatter = editor.realtimeFormatter,
            completionProvider = editor.completionProvider,
            completion = editor.completion

        let shouldDismissCompletionOnCursorActivity = false

        function getNTokens(n, pos) {
            const tokens = Array(n)
            for (let i = 0; i < n; i++) {
                try {
                    const token = cm.getTokenAt(pos, true)
                    tokens[i] = token
                    pos.ch = token.start
                } catch (e) {
                    break
                }
            }
            return tokens
        }

        // cut event is handled in LayeredKeyboardControl via cmd-X hotkey,
        // because we cannot get the content just cut on the cut event.
        cm.on('copy', cm => {
            let selection = cm.getSelection()
            if (!selection) selection = cm.getLine(cm.getCursor().line) + '\n'
            g.macro.addClipboardItem(selection)
        })

        cm.on('scroll', () => {
            completion.set({
                open: false
            })
        })

        cm.on('focus', () => {
            editor.ws.send({
                cmd: 'mtime'
            })
            g.setFocus([g.panelMiddle, editor])
        })
        
        cm.on('blur', () => {
            editor.completion.set({
                open: false
            })
        })

        cm.on('gutterClick', (cm, line, gutter /*, event*/ ) => {
            if (gutter !== 'CodeMirror-linenumbers') return
            const lineLength = cm.getLine(line).length
            cm.setSelection({
                line,
                ch: 0
            }, {
                line,
                ch: lineLength
            })
        })

        cm.on('cursorActivity', cm => {
            if (shouldDismissCompletionOnCursorActivity) {
                completionProvider.state = CLOSED
                completion.set({
                    open: false
                })
            }
            shouldDismissCompletionOnCursorActivity = true
            const cursor = cm.getCursor()
            g.cursorPosition.set(cursor)
            g.docs.getFunctionDocIfNeeded(cm, editor, cursor)
        })

        doc.on('change', (doc /*, changeObj*/ ) => {
            const { clean } = editor.get()
            if (clean === doc.isClean()) return
            editor.set({
                clean: !clean
            })
        })

        cm.on('changes', (cm, c) => {
            if (c[0].origin === 'setValue') return
            const cursor = doc.getCursor()
            const lineContent = cm.getLine(cursor.line)
            const indent = this.ensureIndent
            this.ensureIndent = undefined
            if (indent !== undefined) {
                const diff = indent - cursor.ch
                if (diff > 0)
                    cm.doc.replaceRange(' '.repeat(diff), cursor, cursor)
                else if (diff < 0)
                    cm.execCommand('indentLess')
            }
            // handles Jedi sync if the change isn't a single-char input
            const origin = c[0].origin
            if (origin !== '+input' && origin !== '+completion' && origin !== '+delete') {
                completionProvider.sync(doc.getValue())
            } else if (
                (completionProvider.state === TRIGGERED || completionProvider.state === RETRIGGERED) &&
                (origin === '+input' || origin === '+delete')
            ) {
                completionProvider.retrigger({ lineContent, ...cursor })
            } else if (completionProvider.state === CLOSED) {
                let minLine = Number.MAX_VALUE,
                    maxLine = 0
                for (const ci of c) {
                    minLine = Math.min(minLine, ci.from.line, ci.to.line)
                    maxLine = Math.max(maxLine, ci.from.line, ci.to.line)
                }
                for (let line = minLine, end = maxLine; line <= end; line++) {
                    completionProvider.syncLine(doc.getLine(line), line)
                }
            }
        })

        cm.on('beforeChange', (cm, c) => {
            formatter.setContext(cm, c)
            if (editor.debug) console.log('beforeChange', c)
            const startTime = performance.now()
            try {
                const cursor = c.from
                const lineContent = cm.doc.getLine(cursor.line)
                if (c.origin === '+input') {
                    let input = c.text[0]
                    const [t0, t1, t2] = getNTokens(3, {
                        line: c.from.line,
                        ch: c.from.ch
                    })
                    completionProvider.ruleBasedPredictor.setContext({
                        t0, t1, t2
                    })

                    // for forcing passive in function definition
                    let isInFunctionSignatureDefinition = false
                    let forcePassiveCompletion = false
                    // if it is not single char input, handle by completionProvider.sync()
                    if (c.text.length === 1 &&
                        c.from.line === c.to.line &&
                        input.length === 1
                    ) {
                        // def foo(shouldDisplayPassiveCompletionHere)
                        const currentState = cm.getTokenAt(c.from).state
                        if (currentState.scopes) {
                            const currentScope = currentState.scopes[currentState.scopes.length - 1]
                            if (currentScope.type === ')') {
                                let pos = cm.scanForBracket(c.from, -1, undefined, {
                                    bracketRegex: /[()]/
                                }).pos
                                // eslint-disable-next-line
                                const [tr1, tr2, tr3] = getNTokens(3, pos)
                                if (tr3.string === 'def')
                                    isInFunctionSignatureDefinition = true
                                if (isInFunctionSignatureDefinition && t0.string !== '=')
                                    forcePassiveCompletion = true
                            }
                        }
                        if (!cm.somethingSelected())
                            formatter.inputHandler(lineContent, t0, t1, t2, isInFunctionSignatureDefinition)

                        // TODO: move completionProvider above formatter
                        input = c.text[0]  // might change after handled by formatter, so reassign
                        const isInputDot = /\./.test(input)
                        const ch0 = cursor.ch === 0 ? '' : lineContent[cursor.ch - 1]
                        const inputShouldTriggerPrediction = (
                            t0.type !== 'number' && (
                                (/[A-Za-z_]/.test(input) &&
                                    !/[A-Za-z_]/.test(ch0) &&
                                    completionProvider.state === CLOSED
                                ) || isInputDot
                            )
                        )
                        // handle completion and predictions
                        const newCursor = { line: cursor.line, ch: cursor.ch + input.length }
                        const newLineContent = lineContent.slice(0, cursor.ch) + input + lineContent.slice(cursor.ch)
                        shouldDismissCompletionOnCursorActivity = false
                        
                        if (inputShouldTriggerPrediction) {
                            completionProvider.trigger(
                                newLineContent,
                                newCursor.line,
                                newCursor.ch,
                                -(!isInputDot)
                            )
                            if (t0.type === 'string' ||
                                t0.type === 'comment' ||
                                t1.string === 'for' // for var_name in ... should not complete var_name
                            ) {
                                completionProvider.passive = true
                            } else {
                                completionProvider.passive = forcePassiveCompletion
                            }
                        }
                    } else {
                        formatter.inputHandler(lineContent, t0, t1, t2, isInFunctionSignatureDefinition)
                    }
                } else if (c.origin === '+delete') {
                    shouldDismissCompletionOnCursorActivity = false
                    formatter.deleteHandler()
                }
            } catch (e) {
                console.error(e)
            }
            const timeElapsed = performance.now() - startTime
            if (editor.debug) console.log('beforeChange took', timeElapsed)
            if (timeElapsed > 5) console.warn('slow', c, timeElapsed)
        })
    }

    setIndentAfterChange(n) {
        this.ensureIndent = n
    }
}

export default CMEventDispatcher
