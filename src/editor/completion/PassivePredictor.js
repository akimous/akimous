import Sorter from './Sorter'

class PassivePredictor {
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
    
    send(word, line, ch, triggerdCharOffset) {
        if (!this.enabled) return
        this.startTime = performance.now()
        this.firstTriggeredCharPos.line = line
        this.firstTriggeredCharPos.ch = ch + triggerdCharOffset
        this.word = word
        this.editor.ws.send({
            cmd: 'passive-predict',
            word,
            line,
            ch
        })
    }
}