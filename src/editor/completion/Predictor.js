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

    send(lineContent, line, ch) {
        if (!this.enabled) return
        this.startTime = performance.now()
        this.firstTriggeredCharPos.line = line
        this.firstTriggeredCharPos.ch = ch - 1
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

    repositionCompletionWindow() {
        const rem = parseFloat(getComputedStyle(document.documentElement).fontSize)
        const coords = this.editor.cm.charCoords(this.firstTriggeredCharPos, 'window')
        const editorArea = this.editor.getBoundingClientRect()
        const completionArea = this.completion.getBoundingClientRect()
        // const completionWidth = completionArea.right - completionArea.left
        const completionHeight = completionArea.bottom - completionArea.top
        let x = coords.left - 3 * rem
        let y = coords.bottom + .3 * rem
        if (y + completionHeight > editorArea.bottom) y = coords.top - completionHeight - .3 * rem
        this.completion.style.left = x + 'px'
        this.completion.style.top = y + 'px'
    }

    receive(data) {
        const input = this.lineContent[this.firstTriggeredCharPos.ch]
        if (Predictor.debug) console.log('Predictor.recieve', data)
        this.currentCompletions = data.result
        if (data.result.length < 1) return this.completion.close()
        this.sort(input)
        const shouldDisplayCompletion = this.completion.setCompletions(this.currentCompletions)
        if (shouldDisplayCompletion) {
            this.completion.open()
            this.repositionCompletionWindow()
        } else this.completion.close()
    }

    sort(input) {
        this.sorter.setInput(input)
        for (let i of this.currentCompletions) {
            i.sortScore = this.sorter.score(i.c) * 10
            i.highlight = this.sorter.highlight()
        }
        this.currentCompletions.sort((a, b) => b.sortScore - a.sortScore + b.s - a.s)
        if (Predictor.debug) console.log('Predictor.sort', this.currentCompletions)
    }
}

export default Predictor