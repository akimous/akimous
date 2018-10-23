import { highlightSequentially, inSomething } from '../../lib/Utils'
import { scanInSameLevelOfBraces } from '../EditorFunctions'

const RIGHT_HALVES = new Set([',', ')', ']', '}'])

function sameAsAbove({ topHit, cm, line }) {
    if (!topHit) return

    const topHitCompletion = topHit.c
    const lineCount = cm.lineCount()
    let lineUp = line - 1
    let lineDown = line + 1
    let lineTarget = -1
    let lineContent = ''
    let index = -1

    // find the nearest line including topHit.c
    while (lineUp >= 0 || lineDown < lineCount) {
        if (lineUp >= 0) {
            lineContent = cm.getLine(lineUp)
            index = lineContent.indexOf(topHitCompletion)
            if (index >= 0) {
                lineTarget = lineUp
                break
            }
            lineUp -= 1
        }
        if (lineDown < lineCount) {
            lineContent = cm.getLine(lineDown)
            index = lineContent.indexOf(topHitCompletion)
            if (index >= 0) {
                lineTarget = lineDown
                break
            }
            lineDown += 1
        }
    }
    if (index === -1) return

    const result = scanInSameLevelOfBraces(cm, {
        line: lineTarget,
        ch: index
    }, (cm, char, pos) => {
        if (pos.line !== lineTarget)
            return lineContent.length
        if (RIGHT_HALVES.has(char))
            return pos.ch
    }, 1)

    if (result)
        return lineContent.substring(index, result)
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
    if (!result) return
    return topHit.c + result
}

function fromImport({ lineContent, topHit }) {
    if (!topHit) return
    if (topHit.t !== 'module') return
    if (!/^\s*from/.test(lineContent)) return
    if (/\simport\s/.test(lineContent)) return
    return topHit.c + ' import '
}

function importAs({ lineContent, topHit }) {
    if (!topHit) return
    if (!/import/.test(lineContent)) return
    if (/\sas\s/.test(lineContent)) return
    return topHit.c + ' as '
}

function isNone({ input }) {
    if (input === 'is')
        return 'is None'
}

function isNot({ input }) {
    if (input === 'isn' || input === 'isnt')
        return 'is not '
}

function args({ cm, input, line, ch, lineContent }) {
    if (input !== '*') return
    const openBrace = inSomething(cm, { line, ch }, '(', ')')
    if (!openBrace) return
    let openLine = lineContent
    if (openBrace.line !== line)
        openLine = cm.getLine(openBrace.line)
    if (!/\s*def\s/.test(openLine)) return
    const lastChar = lineContent.charAt(ch - 2)
    if (lastChar === '*')
        return '*kwargs'
    return ['*args', '*args, **kwargs']
}

class RuleBasedPredictor {
    constructor(cm) {
        this.cm = cm
        this.context = { cm }
        this.predictors = [
            sameAsAbove,
            fixedPrediction,
            fromImport,
            importAs,
            isNone,
            isNot,
            args,
        ]
    }

    setContext(context) {
        Object.assign(this.context, context)
    }

    predict(context) {
        context = Object.assign(this.context, context)
        const { input } = context

        context.lineContent = context.cm.getLine(context.line)
        console.log(context)

        const result = []
        this.predictors.forEach(predictor => {
            try {
                const predict = predictor(context)
                if (!predict) return
                if (Array.isArray(predict))
                    result.splice(-1, 0, ...predict)
                else result.push(predict)
            } catch (e) {
                console.error(e)
            }
        })
        return result.map(c => {
            return {
                c,
                t: 'full-statement',
                s: 0,
                sortScore: 0,
                highlight: highlightSequentially(c, input)
            }
        })
    }

}

export default RuleBasedPredictor
