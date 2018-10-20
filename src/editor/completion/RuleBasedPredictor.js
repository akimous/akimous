import { highlightSequentially } from '../../lib/Utils'

function sameAsAbove({lineContent, l1, topHit}) {
    if (!topHit) return
    const index = l1.indexOf(topHit.c)
    
    if (index >= 0) {
        const tail = l1.substring(index)
        return tail
    }
}

const fixedPredictionRules = {
    'import': {
        'matplotlib': '.pyplot as plt',
        'numpy': ' as np',
        'pandas': ' as pd',
        'seaborn': ' as sns',
        'tensorflow': ' as tf',
    }
}
function fixedPrediction({ t2, t1, topHit }) {
    if (!topHit || !t1) return
    let leftToken = t1.string
    if (leftToken.trim().length === 0)
        leftToken = t2.string
    let result = fixedPredictionRules[leftToken]
    if (!result) return
    result = result[topHit.c]
    return topHit.c + result
}

class RuleBasedPredictor {
    constructor(cm) {
        this.cm = cm
        this.context = {}
        this.predictors = [
            sameAsAbove,
            fixedPrediction
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
        const result = this.predictors.map(predictor => {
            try {
                return predictor(context)
            } catch (e) {
                console.error(e)
            }
        }).filter(x => x).map(c => {
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
