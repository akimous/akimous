import Sorter from './Sorter'

class Predictor {
    static get debug() {
        return false
    }

    constructor(editor) {
        this.editor = editor
        this.completion = editor.completion
        this.sorter = new Sorter()
        this.enabled = true
        this.passive = false
        this.firstTriggeredCharPos = {
            line: 0,
            ch: 0
        }
        this.lineContent = ''
        this.isClassDefinition = false
        this.currentCompletions = []
        this.input = ''
        
        editor.ws.addHandler('predict-result', (data) => {
            const input = this.lineContent[this.firstTriggeredCharPos.ch]
            if (Predictor.debug) console.log('Predictor.recieve', data)
            this.currentCompletions = data.result
            if (data.result.length < 1)
                return this.completion.set({
                    open: false
                })
            console.log(this.sortAndFilter(input))
            this.completion.setCompletions(this.sortAndFilter(input), this.firstTriggeredCharPos, this.passive)
        })
        editor.ws.addHandler('predictExtra-result', (data) => {
            const { result } = data
            result.forEach(i => i.highlight = i.c)
            this.completion.setCompletions(result, this.firstTriggeredCharPos, true)
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
        if (this.firstTriggeredCharPos.ch === ch) {
            this.completion.set({
                open: false
            })
            return
        }
        const input = lineContent.slice(this.firstTriggeredCharPos.ch, ch)
        this.input = input
        let completions = this.sortAndFilter(input)
        if (!completions.length) {
            this.editor.ws.send({
                cmd: 'predictExtra',
                input,
                line,
                ch,
            })
        }
        else
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
        console.warn('sync line')
    }

    receive(data) {
        const input = this.lineContent[this.firstTriggeredCharPos.ch]
        if (Predictor.debug) console.log('Predictor.recieve', data)
        this.currentCompletions = data.result
        if (data.result.length < 1)
            return this.completion.set({
                open: false
            })
        this.completion.setCompletions(this.sortAndFilter(input), this.firstTriggeredCharPos, this.passive)
    }

    sortAndFilter(input) {
        if (!input) { // for prediction immediately after dot
            this.currentCompletions.forEach(i => {
                i.sortScore = 1
                i.highlight = i.c
            })
        } else {
            this.sorter.setInput(input)
            for (let i of this.currentCompletions) {
                i.sortScore = this.sorter.score(i.c) * 10
                i.highlight = this.sorter.highlight()
            }
        }
        this.currentCompletions.sort((a, b) => b.sortScore - a.sortScore + b.s - a.s)
        if (Predictor.debug) console.log('Predictor.sort', this.currentCompletions)

        const { passive } = this.completion.get()
        const filteredCompletions = this.currentCompletions.filter(row => {
            if (passive && row.c.length < 3) return false
            return row.sortScore > 0
        })
        return filteredCompletions
    }
}

export default Predictor
