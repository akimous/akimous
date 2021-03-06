import g from '../lib/Globals'
import {
    CLOSED,
    TRIGGERED,
    RESPONDED,
    RETRIGGERED,
    NORMAL,
    STRING,
    COMMENT,
    FOR,
    PARAMETER_DEFINITION,
    AFTER_OPERATOR,
} from './completion/CompletionProvider'
import { OPERATOR } from './RegexDefinitions'
import { schedule, nextFrame, getRem } from '../lib/Utils'

const NONE = -1
const OFFSET_BYPASS_TOKEN_TYPES = new Set(['operator', 'punctuation'])

class CMEventDispatcher {
    constructor(editor) {
        const cm = editor.cm,
            doc = cm.doc,
            formatter = editor.realtimeFormatter
        const { completionProvider, completion, context } = editor

        this.realtimeEvaluation = false
        this.realtimeFormatting = true
        this._indentDelta = 0

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

        // cut event is handled in LayeredKeyboardControl via command-X hotkey,
        // because we cannot get the content just cut on the cut event.
        cm.on('copy', cm => {
            let selection = cm.getSelection()
            if (!selection) selection = cm.getLine(cm.getCursor().line) + '\n'
            g.macro.addClipboardItem(selection)
            completion.$set({ open: false })
        })

        cm.on('scroll', () => {
            completion.$set({ open: false })
        })

        cm.on('focus', () => {
            // prevent panel clicks (e.g. in Docs) to interfere with focus
            nextFrame(() => {
                editor.session.send('Mtime', {})
                g.setFocus([g.panelMiddle, editor])
                if (g.find.active)
                    g.find.clearSelections()
            })
            editor.$set({
                highlightOverlay: null,
                textMark: null,
            })
        })

        //cm.on('blur', () => {
        // editor.completion.$set({ open: false })
        //})

        cm.on('gutterClick', (cm, line, gutter /*, event*/ ) => {
            if (gutter !== 'CodeMirror-linenumbers') return
            const lineLength = cm.getLine(line).length
            cm.setSelection({ line, ch: 0 }, { line, ch: lineLength })
        })

        cm.on('cursorActivity', cm => {
            if (shouldDismissCompletionOnCursorActivity) {
                completionProvider.state = CLOSED
                completion.$set({ open: false })
            }
            shouldDismissCompletionOnCursorActivity = true
            const cursor = cm.getCursor()

            const movingToDifferentLine = cursor.line !== dirtyLine
            if (movingToDifferentLine)
                syncIfNeeded(dirtyLine)

            schedule(() => {
                g.cursorPosition.$set(cursor)
                g.docs.getFunctionDocIfNeeded(cm, editor, cursor)
                const pos = { currentLine: cursor.line }
                g.outline.$set(pos)
                g.linter.$set(pos)
                g.find.$set(pos)
            })

            if (this.realtimeEvaluation)
                g.console.evaluatePartA(cursor.line)
        })

        doc.on('change', (doc /*, changeObj*/ ) => {
            const { clean } = editor // 0.02 ms
            if (clean === doc.isClean()) return
            editor.$set({ clean: !clean }) // 0.25 ms
        })

        cm.on('changes', (cm, changes) => {
            if (!this.realtimeFormatting) return
            const { origin } = changes[0]
            if (origin === 'setValue') return
            const cursor = doc.getCursor()
            const lineContent = cm.getLine(cursor.line)

            // adjust indent
            let i = this._indentDelta
            this._indentDelta = 0 // must set to 0 immediately or it will run into infinite loop
            while (i > 0) {
                cm.execCommand('indentMore')
                i -= 1
            }
            while (i < 0) {
                cm.execCommand('indentLess')
                i += 1
            }

            // handles Jedi sync if the change isn't a single-char input
            const { state } = completionProvider
            if (origin !== '+input' && origin !== '+completion' && origin !== '+delete') {
                syncIfNeeded(changes)
            } else if (
                (state === TRIGGERED || 
                 state === RESPONDED ||
                 state === RETRIGGERED) &&
                (origin === '+input' || origin === '+delete')
            ) {
                completionProvider.retrigger({ lineContent, ...cursor })
            } else if (state === CLOSED) {
                syncIfNeeded(changes)
            }
            if (this.realtimeEvaluation)
                g.console.evaluatePartB(cursor.line, lineContent)
        })

        cm.on('beforeChange', (cm, c) => {
            if (!this.realtimeFormatting) return
            formatter.setContext(cm, c)
            // console.log('beforeChange', c)
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
                    Object.assign(context, { t0, t1, t2, inParentheses: null, inBrackets: null })

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
                                context.inParentheses = { ...pos } // must copy, or getNTokens will change it
                                // eslint-disable-next-line
                                const [tr1, tr2, tr3] = getNTokens(3, pos)
                                if (tr3.string === 'def')
                                    isInFunctionSignatureDefinition = true
                                if (isInFunctionSignatureDefinition && t0.string !== '=')
                                    completionProvider.mode = PARAMETER_DEFINITION
                            } else if (currentScope.type === ']') {
                                let { pos } = cm.scanForBracket(c.from, -1, undefined, {
                                    bracketRegex: /[[\]]/
                                })
                                context.inBrackets = pos
                            }
                        }
                        if (!cm.somethingSelected()) {
                            formatter.inputHandler(lineContent, t0, t1, t2, isInFunctionSignatureDefinition)
                        }
                        input = c.text[0] // might change after handled by formatter, so reassign
                        const isInputDot = input === '.'
                        const isInputOperator = OPERATOR.test(input)
                        const shouldTriggerPrediction = () => {
                            if (c.canceled) return false
                            if (isInputDot && (t0.type === 'variable' || t0.type === 'variable-2')) return true
                            if (t0.type === 'number') return false
                            if (t0.string === '@' && input.length === 1) return true // handle decorator
                            if (completionProvider.state !== CLOSED) return false
                            if (/[A-Za-z_=+\-*/|&^~%@><!]$/.test(input)) return true
                            return false
                        }
                        // handle completion and predictions
                        const newCursor = { line: c.from.line, ch: c.from.ch + input.length }
                        const newLineContent = lineContent.slice(0, c.from.ch) + input + lineContent.slice(c.to.ch)
                        shouldDismissCompletionOnCursorActivity = false
                        if (shouldTriggerPrediction()) {
                            let offset = c.from.ch - c.to.ch
                            if (isInputOperator) // AFTER_OPERATOR case
                                offset = 0
                            else if (!isInputDot) {
                                offset -= 1
                                // avoid completion not offset properly if starts at the middle of a token
                                if (!OFFSET_BYPASS_TOKEN_TYPES.has(t0.type) && !/\s+/.test(t0.string)) {
                                    offset -= t0.string.length
                                }
                            }
                            completionProvider.trigger(
                                newLineContent,
                                newCursor.line,
                                newCursor.ch,
                                offset
                            )
                            dirtyLine = NONE
                            // t0 can be of type string in ''.|
                            // must make sure cursor is inside string, not after
                            if (t0.type === 'string' && cursor.ch < t0.end) completionProvider.mode = STRING
                            else if (t0.type === 'comment') completionProvider.mode = COMMENT
                            // must go after the first two, or completion will not be passive inside strings/comments
                            // int(1, base=|)
                            else if (isInputDot) completionProvider.mode = NORMAL
                            else if (isInputOperator) completionProvider.mode = AFTER_OPERATOR
                            else if (t1.string === 'for') completionProvider.mode = FOR
                            else if (/\s*for\s/.test(newLineContent) && 
                                     !/\sin\s/.test(newLineContent) &&
                                     !(t0.string === ' ' && t1.type === 'variable')) {
                                completionProvider.mode = FOR
                            } else completionProvider.mode = NORMAL
                        } // retrigger is handled in change event
                    } else {
                        formatter.inputHandler(lineContent, t0, t1, t2, isInFunctionSignatureDefinition)
                    }
                } else if (c.origin === '+completion') {
                    let isInFunctionSignatureDefinition = false
                    const [t0, t1, t2] = getNTokens(3, {
                        line: c.from.line,
                        ch: c.from.ch
                    })
                    formatter.inputHandler(lineContent, t0, t1, t2, isInFunctionSignatureDefinition)
                } else if (c.origin === '+delete') {
                    shouldDismissCompletionOnCursorActivity = false
                    formatter.deleteHandler()
                } else if (c.origin === 'paste') {
                    let isInFunctionSignatureDefinition = false
                    const [t0, t1, t2] = getNTokens(3, {
                        line: c.from.line,
                        ch: c.from.ch
                    })
                    formatter.inputHandler(lineContent, t0, t1, t2, isInFunctionSignatureDefinition)
                }
            } catch (e) {
                console.error(e)
            }
            const timeElapsed = performance.now() - startTime
            // console.log('beforeChange took', timeElapsed)
            if (timeElapsed > 5) console.warn('slow', c, timeElapsed)
        })

        cm.on('contextmenu', (cm, event) => {
            const cursor = cm.coordsChar({ left: event.x - 1, top: event.y - 1 })
            if (!event.ctrlKey && !event.metaKey && !event.altKey) {
                const rem = getRem()
                g.contextMenu.$set({
                    open: true,
                    x: event.clientX,
                    y: event.clientY + rem,
                    items: [
                        {
                            text: 'Assignments',
                            icon: 'fas fa-equals',
                            callback: () => {
                                editor.findReferences(['assignments'], cursor)
                            }
                        }, {
                            text: 'Usages',
                            icon: 'fas fa-hand-point-right',
                            callback: () => {
                                editor.findReferences(['usages'], cursor)
                            }
                        }, {
                            text: 'Assignments and Usages',
                            icon: '',
                            callback: () => {
                                editor.findReferences(['assignments', 'usages'], cursor)
                            }
                        },
                    ],
                })
                event.preventDefault()
                event.codemirrorIgnore = false
                return
            }
            const type = []
            if (event.ctrlKey || event.metaKey) {
                type.push('assignments')
            }
            if (event.altKey) {
                type.push('usages')
            }
            editor.findReferences(type, cursor)
            event.preventDefault()
        })
    }

    adjustIndent(n) {
        this._indentDelta = n
    }
}

export default CMEventDispatcher
