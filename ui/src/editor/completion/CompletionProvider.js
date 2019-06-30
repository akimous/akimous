import Sorter from './Sorter'
import RuleBasedPredictor from './RuleBasedPredictor'
import { highlightSequentially } from '../../lib/Utils'

// state
const CLOSED = 0,
    TRIGGERED = 1,
    RESPONDED = 2,
    RETRIGGERED = 3
const NORMAL = 0,
    STRING = 1,
    COMMENT = 2,
    FOR = 3,
    PARAMETER_DEFINITION = 4,
    AFTER_OPERATOR = 5
const debug = false

const shouldUseSequentialHighlighter = new Set([
    'word-segment',
    'word',
    'full-statement'
])

const tails = {
    'class': '()',
    'function': '()',
    // 'param': '=',  // not reliable, see predict in editor.py
    // 'word': ' = ',  // handled in addTail()
    // 'word-segment': ' = ',  // handled in addTail()
    // 'token': ' = ',  // handled in addTail()
    'keyword': ' ',
    'module': ' ',
    'variable': ' ',
}

const passiveTokenCompletionSet = new Set(['word', 'word-segment', 'token'])

class CompletionProvider {
    static get debug() {
        return false
    }

    set passive(x) {
        console.error('set passive')
    }
    get passive() {
        console.error('get passive')
        return false
    }

    //    set type(x) {
    //        this._type = x
    //        console.warn('set type', x)
    //    }
    //    
    //    get type() {
    //        return this._type
    //    }

    //    set state(x) {
    //        this._state = x
    //        console.warn('set state', x)
    //    }
    //
    //    get state() {
    //        return this._state
    //    }

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
        this.lineContent = ''
        this.isClassDefinition = false
        this.currentCompletions = []
        this.input = ''
        this.retriggerQueue = []

        editor.session.handlers['Prediction'] = data => {
            if (debug) console.log('CompletionProvider.receive', data)
            let input = this.lineContent[this.firstTriggeredCharPos.ch]
            this.state = RESPONDED
            this.currentCompletions = data.result
            if (data.result.length < 1) {
                this.state = CLOSED
                this.completion.set({ open: false })
                // do not return here, or 
                // def some|
                // will not work
            }

            if (this.mode === AFTER_OPERATOR)
                input = null
            const sortedCompletions = this.sortAndFilter(input, this.currentCompletions)

            if (this.mode === NORMAL) {
                const ruleBasedPrediction = this.ruleBasedPredictor.predict({
                    topHit: sortedCompletions[0],
                    completions: sortedCompletions,
                    input
                })
                sortedCompletions.splice(1, 0, ...ruleBasedPrediction)
            }
            this.completion.setCompletions(
                sortedCompletions,
                this.firstTriggeredCharPos,
                this.mode
            )
            
            const lastRetriggerJob = this.retriggerQueue.pop()
            this.retriggerQueue.length = 0
            if (lastRetriggerJob)
                this.retrigger(lastRetriggerJob)
        }
        editor.session.handlers['ExtraPrediction'] = ({ result }) => {
            const sortedCompletions = this.sortAndFilter(this.input, result)
            this.completion.setCompletions(
                sortedCompletions,
                this.firstTriggeredCharPos,
                this.mode
            )
        }
    }

    trigger(lineContent, line, ch, triggeredCharOffset) {
        if (!this.enabled) return
        this.startTime = performance.now()
        this.firstTriggeredCharPos.line = line
        this.firstTriggeredCharPos.ch = ch + triggeredCharOffset
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
    }

    retrigger({ lineContent, line, ch }) {
        if (!this.enabled) return
        if (this.firstTriggeredCharPos.ch === ch - 1)
            return // should not do anything if it is just triggered and nothing else is typed
        if (this.state === TRIGGERED) {
            // enqueue retrigger requests if there's any in-flight requests
            this.retriggerQueue.push({ lineContent, line, ch })
            return
        }
        if (this.firstTriggeredCharPos.ch === ch) {
            this.completion.set({ open: false })
            this.state = CLOSED
            return
        }
        this.state = RETRIGGERED
        const input = lineContent.slice(this.firstTriggeredCharPos.ch, ch)
        this.input = input
        let sortedCompletions = this.sortAndFilter(input, this.currentCompletions)

        const ruleBasedPrediction = this.ruleBasedPredictor.predict({
            topHit: sortedCompletions[0],
            completions: sortedCompletions,
            input
        })
        sortedCompletions.splice(1, 0, ...ruleBasedPrediction)

        if (!sortedCompletions.length) {
            this.editor.session.send('PredictExtra', [line, ch, input])
        } else
            this.completion.setCompletions(sortedCompletions, this.firstTriggeredCharPos, this.mode)
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
        if (debug) console.log('CompletionProvider.sort', completions)

        const { type } = this.completion.get()
        const filteredCompletions = completions.filter(row => {
            if (type !== NORMAL && row.text.length < 2) return false
            return row.sortScore > 0
        })
        filteredCompletions.forEach(this.addTail, this)
        return filteredCompletions
    }

    addTail(completion) {
        const { type } = completion
        const { mode } = this
        let tail = tails[type]
        const { lineContent, firstTriggeredCharPos } = this.context
        if (mode === STRING || mode === COMMENT)
            tail = null
        else if (passiveTokenCompletionSet.has(type)) {
            if (mode === PARAMETER_DEFINITION) tail = '='
            else {
                const head = lineContent.substring(0, firstTriggeredCharPos.ch)
                if (/^\s*def\s$/.test(head)) tail = '()'
                else if (!/^\s*$/.test(head)) tail = null
            }
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
