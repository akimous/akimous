import { highlightSequentially } from '../../lib/Utils'

function sameAsAbove({lineContent, l1, topHit}) {
    if (!topHit) return
    const index = l1.indexOf(topHit.c)
    
    if (index >= 0) {
        const tail = l1.substring(index)
        return tail
    }
}

class RuleBasedPredictor {
    constructor(cm) {
        this.cm = cm
        this.context = {}
        this.predictors = [
            sameAsAbove
        ]
    }

    setContext(context) {
        Object.assign(this.context, context)
    }
    
    predict(context) {
        const cm = this.cm
        context = Object.assign(this.context, context)
        const { line, ch, input } = context
        const l1 = cm.getLine(line - 1)
        
        Object.assign(context, { l1 })
        
        console.log(context)
        const result = this.predictors.map(predictor => predictor(context))
            .filter(x => x)
            .map(c => {
                return {
                    c, 
                    t: 'full-statement',
                    s: 0,
                    sortScore: 0,
                    highlight: highlightSequentially(c, input)
                }
            })
        return result
    }

}

export default RuleBasedPredictor
