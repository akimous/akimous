import g from '../lib/Globals'
import {
    CLOSED,
    TRIGGERED,
    RETRIGGERED,
    NORMAL,
    STRING,
    COMMENT,
    FOR,
    PARAMETER_DEFINITION,
    AFTER_OPERATOR,
} from './completion/CompletionProvider'
import { OPERATOR } from './RegexDefinitions'
import { schedule, nextFrame } from '../lib/Utils'

const NONE = -1

class CMEventDispatcher {
    constructor(editor) {
        const cm = editor.cm,
            doc = cm.doc,
            formatter = editor.realtimeFormatter,
            completionProvider = editor.completionProvider,
            completion = editor.completion

        let dirtyLine = NONE
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

        function syncIfNeeded(changes) {
            // if has multiple changes exist (e.g. new line), must sync
            if (!Number.isInteger(changes) &&
                (changes[0].text.length > 1 || changes[0].removed.length > 1))
                editor.syncChanges(changes)
            else if (dirtyLine === NONE) return
            else if (Number.isInteger(changes))
                editor.syncChanges(changes, cm.getLine(changes))
            else
                editor.syncChanges(changes)
            dirtyLine = NONE
        }

        // cut event is handled in LayeredKeyboardControl via cmd-X hotkey,
        // because we cannot get the content just cut on the cut event.
        cm.on('copy', cm => {
            let selection = cm.getSelection()
            if (!selection) selection = cm.getLine(cm.getCursor().line) + '\n'
            g.macro.addClipboardItem(selection)
        })

        cm.on('scroll', () => {
            completion.set({ open: false })
        })

        cm.on('focus', () => {
            // prevent panel clicks (e.g. in Docs) to interfere with focus
            nextFrame(() => {
                editor.socket.send('Mtime', {})
                g.setFocus([g.panelMiddle, editor])
                g.find.clearSelections()
            })
            editor.set({
                highlightOverlay: null,
                textMark: null,
            })
        })

        cm.on('blur', () => {
            editor.completion.set({ open: false })
        })

        cm.on('gutterClick', (cm, line, gutter /*, event*/ ) => {
            if (gutter !== 'CodeMirror-linenumbers') return
            const lineLength = cm.getLine(line).length
            cm.setSelection({ line, ch: 0 }, { line, ch: lineLength })
        })

        cm.on('cursorActivity', cm => {
            if (shouldDismissCompletionOnCursorActivity) {
                completionProvider.state = CLOSED
                completion.set({ open: false })
            }
            shouldDismissCompletionOnCursorActivity = true
            const cursor = cm.getCursor()

            const movingToDifferentLine = cursor.line !== dirtyLine
            if (movingToDifferentLine)
                syncIfNeeded(dirtyLine)

            schedule(() => {
                g.cursorPosition.set(cursor)
                g.docs.getFunctionDocIfNeeded(cm, editor, cursor)
                const pos = { currentLine: cursor.line }
                g.outline.set(pos)
                g.linter.set(pos)
                g.find.set(pos)
            })
        })

        doc.on('change', (doc /*, changeObj*/ ) => {
            const { clean } = editor.get() // 0.02 ms
            if (clean === doc.isClean()) return
            editor.set({ clean: !clean }) // 0.25 ms
        })

        cm.on('changes', (cm, changes) => {
            if (changes[0].origin === 'setValue') return
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
            const origin = changes[0].origin
            if (origin !== '+input' && origin !== '+completion' && origin !== '+delete') {
                syncIfNeeded(changes)
            } else if (
                (completionProvider.state === TRIGGERED || completionProvider.state === RETRIGGERED) &&
                (origin === '+input' || origin === '+delete')
            ) {
                completionProvider.retrigger({ lineContent, ...cursor })
            } else if (completionProvider.state === CLOSED) {
                syncIfNeeded(changes)
            }
        })

        cm.on('beforeChange', (cm, c) => {
            formatter.setContext(cm, c)
            if (editor.debug) console.log('beforeChange', c)
            const startTime = performance.now()
            try {
                const cursor = c.from
                dirtyLine = cursor.line
                const lineContent = cm.doc.getLine(cursor.line)
                if (c.origin === '+input') {
                    let input = c.text[0]
                    const [t0, t1, t2] = getNTokens(3, {
                        line: c.from.line,
                        ch: c.from.ch
                    })
                    Object.assign(completionProvider.context, { t0, t1, t2 })

                    // for forcing passive in function definition
                    let isInFunctionSignatureDefinition = false

                    // if it is a single char input
                    if (c.text.length === 1 &&
                        c.from.line === c.to.line &&
                        input.length === 1
                    ) {
                        // def foo(shouldDisplayPassiveCompletionHere)
                        const currentState = cm.getTokenAt(c.from).state
                        if (currentState.scopes) {
                            const currentScope = currentState.scopes[currentState.scopes.length - 1]
                            if (currentScope.type === ')') {
                                let { pos } = cm.scanForBracket(c.from, -1, undefined, {
                                    bracketRegex: /[()]/
                                })
                                // eslint-disable-next-line
                                const [tr1, tr2, tr3] = getNTokens(3, pos)
                                if (tr3.string === 'def')
                                    isInFunctionSignatureDefinition = true
                                if (isInFunctionSignatureDefinition && t0.string !== '=')
                                    completionProvider.type = PARAMETER_DEFINITION
                            }
                        }
                        if (!cm.somethingSelected())
                            formatter.inputHandler(lineContent, t0, t1, t2, isInFunctionSignatureDefinition)

                        // TODO: move completionProvider above formatter
                        input = c.text[0] // might change after handled by formatter, so reassign
                        const isInputDot = /\./.test(input)

                        const inputShouldTriggerPrediction = () => {
                            if (isInputDot) return true
                            if (t0.type === 'number') return false
                            if (completionProvider.state !== CLOSED) return false
                            if (/[A-Za-z_=+\-*/|&^~%@><!]$/.test(input)) return true
                            return false
                        }
                        // handle completion and predictions
                        const newCursor = { line: cursor.line, ch: cursor.ch + input.length }
                        const newLineContent = lineContent.slice(0, cursor.ch) + input + lineContent.slice(cursor.ch)
                        shouldDismissCompletionOnCursorActivity = false

                        if (inputShouldTriggerPrediction()) {
                            completionProvider.trigger(
                                newLineContent,
                                newCursor.line,
                                newCursor.ch,
                                -(!isInputDot)
                            )
                            dirtyLine = NONE
                            if (t0.type === 'string') completionProvider.type = STRING
                            else if (t0.type === 'comment') completionProvider.type = COMMENT
                            else if (t1.string === 'for') completionProvider.type = FOR
                            else if (OPERATOR.test(input)) completionProvider.type = AFTER_OPERATOR
                            else completionProvider.type = NORMAL
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
