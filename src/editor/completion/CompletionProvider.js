import Sorter from './Sorter'
import RuleBasedPredictor from './RuleBasedPredictor'
import { highlightSequentially, inParentheses } from '../../lib/Utils'

const CLOSED = 0,
    TRIGGERED = 1,
    RETRIGGERED = 2
const debug = false

const shouldUseSequentialHighlighter = new Set([
    'word-segment',
    'word',
    'full-statement'
])

const tails = {
    'class': '()',
    'function': '()',
    // 'param': '=', // `if p=` is wrong, when p is a function parameter, but it is not calling
    'word': ' = ',
    'word-segment': ' = ',
    'token': ' = ',
    'keyword': ' ',
    'module': ' ',
    'variable': ' ',
    'param': ' ',
}
function addTail(completion, noSpaceAroundEqualSign = false) {
    const { t } = completion
    let tail = tails[t]
    if (noSpaceAroundEqualSign && tail === ' = ')
        tail = '='
    if (tail)
        completion.tail = tail
}

class CompletionProvider {
    static get debug() {
        return false
    }

    constructor(editor) {
        this.editor = editor
        this.completion = editor.completion
        this.sorter = new Sorter()
        this.ruleBasedPredictor = new RuleBasedPredictor(this.editor.cm)
        this.enabled = true
        this.passive = false
        this.state = CLOSED

        this.firstTriggeredCharPos = {
            line: 0,
            ch: 0
        }
        this.lineContent = ''
        this.isClassDefinition = false
        this.currentCompletions = []
        this.input = ''

        editor.ws.addHandler('predict-result', (data) => {
            if (debug) console.log('CompletionProvider.recieve', data)
            const input = this.lineContent[this.firstTriggeredCharPos.ch]
            this.state = TRIGGERED
            this.currentCompletions = data.result
            if (data.result.length < 1)
                return this.completion.set({
                    open: false
                })
            const sortedCompletions = this.sortAndFilter(input, this.currentCompletions)

            const ruleBasedPrediction = this.ruleBasedPredictor.predict({
                topHit: sortedCompletions[0],
                completions: sortedCompletions,
                input
            })
            sortedCompletions.splice(1, 0, ...ruleBasedPrediction)
            this.completion.setCompletions(
                sortedCompletions,
                this.firstTriggeredCharPos,
                this.passive
            )
        })
        editor.ws.addHandler('predictExtra-result', (data) => {
            const { result } = data
            const sortedCompletions = this.sortAndFilter(this.input, result)
            this.completion.setCompletions(
                sortedCompletions,
                this.firstTriggeredCharPos,
                true // passive
            )
        })
    }

    trigger(lineContent, line, ch, triggerdCharOffset) {
        if (!this.enabled) return
        this.startTime = performance.now()
        this.firstTriggeredCharPos.line = line
        this.firstTriggeredCharPos.ch = ch + triggerdCharOffset
        this.lineContent = lineContent
        this.editor.ws.send({
            cmd: 'predict',
            text: lineContent,
            line,
            ch,
        })
        this.isClassDefinition = /^\s*class\s/.test(lineContent)
        this.ruleBasedPredictor.setContext({
            firstTriggeredCharPos: this.firstTriggeredCharPos,
            lineContent: this.lineContent,
            line,
            ch
        })
    }

    retrigger({ lineContent, line, ch }) {
        console.warn('retriggered')
        if (!this.enabled) return
        if (this.firstTriggeredCharPos.ch === ch) {
            this.completion.set({
                open: false
            })
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
            this.editor.ws.send({
                cmd: 'predictExtra',
                input,
                line,
                ch,
            })
        } else
            this.completion.setCompletions(sortedCompletions, this.firstTriggeredCharPos, this.passive)
    }

    sync(doc) {
        if (!this.enabled) return
        this.editor.ws.send({
            cmd: 'sync',
            doc
        })
        console.warn('syncing')
    }

    syncLine(lineContent, line) {
        if (!this.enabled) return
        this.editor.ws.send({
            cmd: 'syncLine',
            text: lineContent,
            line
        })
    }

    sortAndFilter(input, completions) {
        if (!input) { // for prediction immediately after dot
            completions.forEach(i => {
                i.sortScore = 1
                i.highlight = i.c
            })
        } else {
            this.sorter.setInput(input)
            for (let i of completions) {
                i.sortScore = this.sorter.score(i.c) * 10
                if (shouldUseSequentialHighlighter.has(i.t))
                    i.highlight = highlightSequentially(i.c, input)
                else
                    i.highlight = this.sorter.highlight()
            }
        }
        completions.sort((a, b) => b.sortScore - a.sortScore + b.s - a.s)
        if (debug) console.log('CompletionProvider.sort', completions)

        const { passive } = this.completion.get()
        const filteredCompletions = completions.filter(row => {
            if (passive && row.c.length < 2) return false
            return row.sortScore > 0
        })
        let tail_ = addTail
        if (inParentheses(this.editor.cm, this.firstTriggeredCharPos))
            tail_ = x => addTail(x, true)
        filteredCompletions.forEach(tail_)
        return filteredCompletions
    }
}

export { CompletionProvider, CLOSED, TRIGGERED, RETRIGGERED }
