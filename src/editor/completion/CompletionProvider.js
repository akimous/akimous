import Sorter from './Sorter'

const CLOSED = 0,
    TRIGGERED = 1,
    RETRIGGERED = 2
const debug = false

class CompletionProvider {
    static get debug() {
        return false
    }

    constructor(editor) {
        this.editor = editor
        this.completion = editor.completion
        this.sorter = new Sorter()
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
            this.completion.setCompletions(
                this.sortAndFilter(input, this.currentCompletions),
                this.firstTriggeredCharPos, 
                this.passive
            )
        })
        editor.ws.addHandler('predictExtra-result', (data) => {
            const { result } = data
            this.completion.setCompletions(
                this.sortAndFilter(this.input, result),
                this.firstTriggeredCharPos,
                true  // passive
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
        let completions = this.sortAndFilter(input, this.currentCompletions)
        if (!completions.length) {
            this.editor.ws.send({
                cmd: 'predictExtra',
                input,
                line,
                ch,
            })
        } else
            this.completion.setCompletions(completions, this.firstTriggeredCharPos, this.passive)
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
                i.highlight = this.sorter.highlight()
            }
        }
        completions.sort((a, b) => b.sortScore - a.sortScore + b.s - a.s)
        if (debug) console.log('CompletionProvider.sort', completions)

        const { passive } = this.completion.get()
        const filteredCompletions = completions.filter(row => {
            if (passive && row.c.length < 3) return false
            return row.sortScore > 0
        })
        return filteredCompletions
    }
}

export { CompletionProvider, CLOSED, TRIGGERED, RETRIGGERED }
