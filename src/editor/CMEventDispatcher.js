import g from '../lib/Globals'

class CMEventDispatcher {
    constructor(editor) {
        const cm = editor.cm,
            doc = cm.doc,
            formatter = editor.realtimeFormatter,
            predictor = editor.predictor,
            completion = editor.completion

        let shouldSyncAfterChange = false
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

        cm.on('gutterClick', (cm, line, gutter, event) => {
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

        cm.on('cursorActivity', () => {
            if (shouldDismissCompletionOnCursorActivity) {
                completion.set({
                    open: false
                })
            }
            shouldDismissCompletionOnCursorActivity = true
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
            const indent = this.ensureIndent
            this.ensureIndent = undefined
            if (indent !== undefined) {
                const pos = doc.getCursor()
                const diff = indent - pos.ch
                if (diff > 0)
                    cm.doc.replaceRange(' '.repeat(diff), pos, pos)
                else if (diff < 0)
                    cm.execCommand('indentLess')
            }
            // handles Jedi sync if the change isn't a single-char input
            const origin = c[0].origin
            if (shouldSyncAfterChange ||
                (origin !== '+input' && origin !== '+completion' && origin !== '+delete')) {
                shouldSyncAfterChange = false
                predictor.sync(doc.getValue())
            }
        })

        cm.on('beforeChange', (cm, c) => {
            shouldDismissCompletionOnCursorActivity = false
            formatter.setContext(cm, c)
            if (editor.debug) console.log('beforeChange', c)
            const startTime = performance.now()
            try {
                const cursor = c.from
                const lineContent = cm.doc.getLine(cursor.line)
                if (c.origin === '+input') {
                    const inputChar = c.text[0]
                    // TODO: reuse t0/1/2 in formatter
                    const [t0, t1, t2] = getNTokens(3, {
                        line: c.from.line,
                        ch: c.from.ch
                    })
                    const inputAfterFormatting = c.text[0]

                    // for forcing passive in function definition
                    let isInFunctionSignatureDefinition = false
                    let forcePassiveCompletion = false

                    // if it is not single char input, handle by predictor.sync()
                    if (c.text.length === 1 &&
                        c.from.line === c.to.line &&
                        inputChar.length === 1
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
                        formatter.inputHandler(lineContent, t0, t1, t2, isInFunctionSignatureDefinition)
                        const isInputAlphanumericOrUnderscore = /[A-Za-z0-9_]/.test(inputChar)
                        const isFirstLetter = isInputAlphanumericOrUnderscore && (
                            cursor.ch === 0 ||
                            !/[A-Za-z0-9_]/.test(lineContent.charAt(cursor.ch - 1))
                        )

                        // handle completion and predictions
                        if (isFirstLetter) {
                            const lineContentAfterInput = lineContent.slice(0, cursor.ch) + c.text[0] + lineContent.slice(cursor.ch)
                            predictor.send(
                                lineContentAfterInput,
                                cursor.line,
                                cursor.ch + inputAfterFormatting.length
                            )
                            const currentTokenType = cm.getTokenTypeAt(cursor)
                            if (currentTokenType === 'string' ||
                                currentTokenType === 'comment' ||
                                t1.string === 'for' // for var_name in ... should not complete var_name
                            ) completion.passive = true
                            else completion.passive = forcePassiveCompletion
                        } else if (predictor.currentCompletions) {
                            const input = lineContent.slice(predictor.firstTriggeredCharPos.ch, cursor.ch) + c.text[0]
                            predictor.sort(input)
                            completion.setCompletions()
                        }
                    } else {
                        shouldSyncAfterChange = true
                        formatter.inputHandler(lineContent, t0, t1, t2, isInFunctionSignatureDefinition)
                    }
                    //                        break
                } else if (c.origin === '+delete') {
                    if (c.from.line !== c.to.line) {
                        shouldSyncAfterChange = true
                    } else {
                        formatter.deleteHandler()
                    }
                    if (!completion.get().open) return
                    if (predictor.firstTriggeredCharPos.ch === cursor.ch) {
                        completion.set({
                            open: false
                        })
                        return
                    }
                    const input = lineContent.slice(predictor.firstTriggeredCharPos.ch, cursor.ch)
                    predictor.sort(input)
                    completion.setCompletions(predictor.currentCompletions)
                    return
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
