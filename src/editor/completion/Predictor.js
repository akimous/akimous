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
        this.firstTriggeredCharPos = {
            line: 0,
            ch: 0
        }
        this.lineContent = ''
    }

    send(lineContent, line, ch, triggerdCharOffset) {
        if (!this.enabled) return
        this.startTime = performance.now()
        this.firstTriggeredCharPos.line = line
        this.firstTriggeredCharPos.ch = ch + triggerdCharOffset
        this.lineContent = lineContent
        this.editor.ws.send({
            cmd: 'predict',
            text: lineContent,
            line,
            ch
        })
    }

    sync(doc) {
        if (!this.enabled) return
        this.editor.ws.send({
            cmd: 'sync',
            doc
        })
        console.warn('syncing')
    }

    receive(data) {
        const input = this.lineContent[this.firstTriggeredCharPos.ch]
        if (Predictor.debug) console.log('Predictor.recieve', data)
        this.currentCompletions = data.result
        if (data.result.length < 1)
            return this.completion.set({
                open: false
            })
        this.sort(input)
        this.completion.setCompletions(this.currentCompletions)
        this.completion.repositionCompletionWindow(this.firstTriggeredCharPos)
    }

    sort(input) {
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
    }
}

export default Predictor
