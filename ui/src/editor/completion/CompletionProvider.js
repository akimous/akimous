import camelCase from 'lodash.camelcase'

import g from '../../lib/Globals'
import Sorter from './Sorter'
import RuleBasedPredictor from './RuleBasedPredictor'
import { highlightSequentially } from '../../lib/Utils'

// state
const CLOSED = 0,
    TRIGGERED = 1,
    RESPONDED = 2,
    RETRIGGERED = 3
// mode
const NORMAL = 0,
    STRING = 1,
    COMMENT = 2,
    FOR = 3,
    PARAMETER_DEFINITION = 4,
    AFTER_OPERATOR = 5
const debug = true

const shouldUseSequentialHighlighter = new Set([
    'word-segment',
    'word',
    'full-statement'
])

const tails = {
    'class': '()',
    'function': '()',
    // 'word': ' = ',  // handled in addTail()
    // 'word-segment': ' = ',  // handled in addTail()
    // 'token': ' = ',  // handled in addTail()
    'keyword': ' ',
    'module': ' ',
    'variable': ' ',
    'param': ' ', // probably not reliable, see predict in editor.py
    // 'statement': ' ', // good for `if xxx_and` but bad for `int(xxx|)`
}

const forVariableOffset = {
    'keyword': -2000,
    'module': -1900,
    'class': -1800,
    'function': -1700,
}

const passiveTokenCompletionSet = new Set(['word', 'word-segment', 'token'])

class CompletionProvider {
    static get debug() {
        return false
    }

    //    set mode(x) {
    //        this._mode = x
    //        console.warn('set mode', x)
    //    }
    //    
    //    get mode() {
    //        return this._mode
    //    }

    //    set state(x) {
    //        this._state = x
    //        console.warn('set state', x)
    //    }

    //   get state() {
    //       return this._state
    //   }

    constructor(editor) {
        this.editor = editor
        this.completion = editor.completion
        this.sorter = new Sorter()
        this.context = { cm: this.editor.cm }
        this.ruleBasedPredictor = new RuleBasedPredictor(this.context)
        this.enabled = true
        this.state = CLOSED
        this.mode = NORMAL

        this.firstTriggeredCharPos = {
            line: 0,
            ch: 0
        }
        this.triggeredCharOffset = 0
        this.lineContent = ''
        this.isClassDefinition = false
        this.currentCompletions = []
        this.input = ''
        this.retriggerQueue = []

        editor.session.handlers['Prediction'] = data => {
            if (debug) console.log('CompletionProvider.receive', data)
            const { line, ch } = data
            let input = this.lineContent.slice(this.firstTriggeredCharPos.ch, ch) || ''
            this.input = input
            this.state = RESPONDED
            this.currentCompletions = data.result
            if (data.result.length < 1) {
                this.state = CLOSED
                this.completion.$set({ open: false })
                // do not return here, or 
                // def some|
                // will not work
            }
            if (this.mode === AFTER_OPERATOR)
                input = null
            
            // adjust score, or weird stuff will pop up at positions supposed to be variable
            if (this.mode === FOR) {
                for (const completion of this.currentCompletions) {
                    completion.score += forVariableOffset[completion.type] || 0
                }
            }
            
            const sortedCompletions = this.sortAndFilter(input, this.currentCompletions)

            if (this.mode === NORMAL) {
                this.requestExtraPredictions(line, ch, input, sortedCompletions)
            } else {
                this.deduplicateAndSetCompletions(sortedCompletions)
            }

            const lastRetriggerJob = this.retriggerQueue.pop()
            this.retriggerQueue.length = 0
            if (!lastRetriggerJob) return
            if (lastRetriggerJob.line === data.line && lastRetriggerJob.ch === data.ch) return
            this.retrigger(lastRetriggerJob)
        }
        editor.session.handlers['ExtraPrediction'] = ({ result }) => {
            this.mode = STRING
            
            const { t1, t2, input } = this.context
            if (t2.string === 'def') {
                // decide whether self should be added
                if (this.isMethodDefinition()) {
                    result.forEach(item => {
                        item.tail = '(self)'
                    })
                } else {
                    result.forEach(item => {
                        item.tail = '()'
                    })
                }
            } else if (!t2.type && !t1.type && t2.start === t2.end && !t1.string.trim()) {
                result.forEach(item => {
                    item.tail = ' ='
                })
            }
            
            if (t2.string === 'class' || /[A-Z]/.test(input.charAt(0))) {
                result.forEach(item => {
                    let camel = camelCase(item.text)
                    camel = camel.charAt(0).toUpperCase() + camel.substring(1)
                    item.text = camel
                })
            }
            const sortedCompletions = this.sortAndFilter(this.input, result)
            this.deduplicateAndSetCompletions(sortedCompletions)
        }
    }
    
    isMethodDefinition() {
        const highlightedOutlineItem = g.outline.highlightedItem
        if (!highlightedOutlineItem) return false
        const currentLevel = highlightedOutlineItem.level
        if (!currentLevel) return false
        const { outlineItems } = g.outline
        let i
        for (i = 0; i < outlineItems.length; i++) {
            if (outlineItems[i] === highlightedOutlineItem) break
        }
        if (i === outlineItems.length) return false
        for (i-- ; i >= 0; i--) {
            const { level, type } = outlineItems[i]
            if (level < currentLevel) {
                if (type === 'class') return true
                return false
            }
        }
        return false
    }

    deduplicateAndSetCompletions(sortedCompletions) {
        const set = new Set()
        this.completion.setCompletions(
            sortedCompletions.filter(v => {
                if (set.has(v.text)) return false
                set.add(v.text)
                return true
            }),
            this.firstTriggeredCharPos,
            this.mode
        )
    }

    trigger(lineContent, line, ch, triggeredCharOffset) {
        if (!this.enabled) return
        this.startTime = performance.now()
        this.firstTriggeredCharPos.line = line
        this.firstTriggeredCharPos.ch = ch + triggeredCharOffset
        this.triggeredCharOffset = triggeredCharOffset
        this.lineContent = lineContent
        this.editor.session.send('Predict', [line, ch, lineContent])
        this.isClassDefinition = /^\s*class\s/.test(lineContent)
        Object.assign(this.context, {
            firstTriggeredCharPos: this.firstTriggeredCharPos,
            lineContent: this.lineContent,
            line,
            ch
        })
        this.state = TRIGGERED
        this.retriggerQueue.length = 0 // clear queue
    }
    
    requestExtraPredictions(line, ch, input, sortedCompletions) {
        const ruleBasedPrediction = this.ruleBasedPredictor.predict({
            topHit: sortedCompletions[0],
            completions: sortedCompletions,
            input
        })
        sortedCompletions.splice(1, 0, ...ruleBasedPrediction)

        if (!sortedCompletions.length) {
            this.editor.session.send('PredictExtra', [line, ch, input])
        } else {
            this.deduplicateAndSetCompletions(sortedCompletions)
        }
    }

    retrigger({ lineContent, line, ch }) {
        if (!this.enabled) return
        if (this.triggeredCharOffset && this.firstTriggeredCharPos.ch === ch - 1)
            return // should not do anything if it is just triggered and nothing else is typed
        if (this.state === TRIGGERED) {
            // enqueue retrigger requests if there's any in-flight requests
            this.retriggerQueue.push({ lineContent, line, ch })
            return
        }
        if (this.firstTriggeredCharPos.ch === ch) {
            this.completion.$set({ open: false })
            this.state = CLOSED
            return
        }
        this.state = RETRIGGERED
        const input = lineContent.slice(this.firstTriggeredCharPos.ch, ch)
        this.input = input
        let sortedCompletions = this.sortAndFilter(input, this.currentCompletions)
        this.requestExtraPredictions(line, ch, input, sortedCompletions)
    }

    sortAndFilter(input, completions) {
        if (!input) { // for prediction immediately after dot or operator
            completions.forEach(i => {
                i.sortScore = 1
                i.highlight = i.text
            })
        } else {
            this.sorter.setInput(input)
            for (let i of completions) {
                i.sortScore = this.sorter.score(i.text) * 10
                if (shouldUseSequentialHighlighter.has(i.type))
                    i.highlight = highlightSequentially(i.text, input)
                else
                    i.highlight = this.sorter.highlight()
            }
        }
        completions.sort((a, b) => b.sortScore - a.sortScore + b.score - a.score)
        if (debug) console.log('CompletionProvider.sort', input, completions)

        const { type } = this.completion
        const filteredCompletions = completions.filter(row => {
            if (type !== NORMAL && row.text.length < 2) return false
            return row.sortScore + row.score > 0
        })
        
        // prepare common parts for addTail
        const { lineContent, firstTriggeredCharPos, inParentheses, cm, t0, t1 } = this.context
        this.context.isImport = false
        if (lineContent.includes(' import ')) {
            this.context.isImport = true
        } else if (inParentheses) {
            const pos = {...inParentheses}
            pos.ch -= 2
            const token = cm.getTokenAt(pos)
            if (token && token.string === 'import') {
                this.context.isImport = true
            }            
        }
        const head = lineContent.substring(0, firstTriggeredCharPos.ch)
        Object.assign(this.context, {
            isDef: /^\s*def\s$/.test(head),
            isSpace: /^\s*$/.test(head),
            afterAt: (t0 && t0.string === '@') || (t1 && t1.string === '@'),
            except: /^\s*except\s/.test(head),
        })
        filteredCompletions.forEach(this.addTail, this)
        return filteredCompletions
    }

    addTail(completion) {
        const { type, postfix } = completion
        const { mode } = this
        let tail = tails[type]
        const { isImport, isDef, isSpace, afterAt, except } = this.context
        if (mode === STRING || mode === COMMENT)
            tail = null
        else if (passiveTokenCompletionSet.has(type)) {
            if (mode === PARAMETER_DEFINITION) tail = '='
            else {
                if (isDef) tail = '()'
                else if (!isSpace) tail = null
            }
        } else if (tail === '()') {
            if (isImport) tail = null
            else if (postfix) tail = null
            else if (afterAt) tail = null  // handle @property and other decorators
            else if (except) tail = null
        }
        if (tail)
            completion.tail = tail
    }
}

export {
    CompletionProvider,
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
}
