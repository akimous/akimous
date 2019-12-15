import { Pos } from '../lib/Utils'

// For sharing states between CompletionProvider, RuleBasedPredictor and RealtimeFormatter,
// so that we can get rid of Object.assign().
class Context {
    constructor() {
        this.cm = null
        this.input = ''
        this.line = 0
        this.ch = 0
        this.lineContent = ''
        this.t0 = ''
        this.t1 = ''
        this.t2 = ''
        
        this.triggeredCharOffset = 0
        this.firstTriggeredCharPos = Pos(0, 0)
        
        this.topHit = null
        this.completions = []
        
        this.head = ''
        this.afterAt = false
        this.except = false
        this.inParentheses = null
        this.isClassDefinition = false
        this.isDef = false
        this.isDefParameter = false
        this.isImport = false
    }
    
    bind(cm) {
        this.cm = cm
    }
}

export default Context
