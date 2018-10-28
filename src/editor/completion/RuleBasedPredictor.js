import { highlightSequentially, inSomething } from '../../lib/Utils'
import { scanInSameLevelOfBraces } from '../EditorFunctions'
import snakecase from 'lodash.snakecase'

const RIGHT_HALVES = new Set([',', ')', ']', '}'])
const MAX_SCAN_LINES = 100

function sameAsAbove({ topHit, cm, line }) {
    if (!topHit) return

    const topHitCompletion = topHit.c
    const lineCount = cm.lineCount()
    let lineUp = line - 1
    let lineDown = line + 1
    let targetLine = -1
    let lineContent = ''
    let index = -1

    const containsTopHit = l => {
        lineContent = cm.getLine(l)
        index = lineContent.indexOf(topHitCompletion)
        if (index < 0) return false
        
        const commentStart = lineContent.indexOf('#')
        if (commentStart > 0 && index > commentStart) return false
        
        // previous character is alphanumeric
        if (index > 0 && /\w|\d/.test(lineContent.charAt(index - 1))) return false
        
        if (/\s*import\s/.test(lineContent)) return false
        
        targetLine = l
        return true
    }

    let scannedCount = 0
    // find the nearest line including topHit.c
    while (lineUp >= 0 || lineDown < lineCount) {
        if (lineUp >= 0 && containsTopHit(lineUp--))
            break
        if (lineDown < lineCount && containsTopHit(lineDown++))
            break
        if (scannedCount++ === MAX_SCAN_LINES)
            break
    }
    if (index === -1) return

    const result = scanInSameLevelOfBraces(cm, {
        line: targetLine,
        ch: index
    }, (cm, char, pos) => {
        if (pos.line !== targetLine)
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

function fixedPredictionForImport({ t2, t1, topHit, lineContent }) {
    if (!topHit || !t1) return
    if (!/\s*import\s/.test(lineContent)) return
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

function withAs({ lineContent, topHit }) {
    if (!topHit) return
    if (topHit.c !== 'as') return
    if (!/\s*with\s\w/.test(lineContent)) return
    if (/\s*with open\(/.test(lineContent)) return 'as f: '
    
    // Example:
    // lineContent: with tf.Session(graph=graph) as session:
    // match: with tf.Session(
    // identifier: tf.Session
    // snake: session
    const match = /with\s[\w_][\w\d_.]+(\(|\s)/.exec(lineContent)[0]
    const identifiers = match.substring(5, match.length - 1).split('.')
    const lastIdentifier = identifiers[identifiers.length - 1]
    const snake = snakecase(lastIdentifier)
    return `as ${snake}: `
}

const nextVariablePartMapping = {
    'a': 'b',
    'b': 'c',
    'c': 'd',
    'i': 'j',
    'j': 'k',
    'k': 'l',
    'x': 'y',
    'y': 'z',
}
function nextPossibleVariableName(name) {
    // something_a => something_b
    const splits = name.split('_')
    for (let i = splits.length - 1; i > 0; i--) {
        const part = splits[i]
        if (Number.isInteger(+part)) {
            splits[i] = (+part + 1).toString()
            return splits.join('_')
        } else if (nextVariablePartMapping[part]) {
            splits[i] = nextVariablePartMapping[part]
            return splits.join('_')
        }
    }
    // something1 => something2
    const lastChar = name.charAt(name.length - 1)
    if (Number.isInteger(+lastChar)) {
        const nextNumber = +lastChar + 1
        if (nextNumber < 10)
            return name.substring(0, name.length - 1) + nextNumber
    }
}
function sequentialVariableNaming({ topHit, line, cm, completions }) {
    if (line < 1) return
    if (!topHit) return
    if (topHit.t !== 'statement') return
    const lastLine = cm.getLine(line - 1)
    const index = lastLine.indexOf(topHit.c)
    if (index === -1) return
    if (index + topHit.c.length + 3 >= lastLine.length) return
    const charsAfterTopHitInLastLine = lastLine.substr(index + topHit.c.length, 3)
    if (charsAfterTopHitInLastLine !== ' = ') return
    const result = nextPossibleVariableName(topHit.c)
    if (!result) return
    if (completions.some(i => i.c === result)) return
    return result + ' = '
}

class RuleBasedPredictor {
    constructor(cm) {
        this.cm = cm
        this.context = { cm }
        this.predictors = [
            sameAsAbove,
            fixedPredictionForImport,
            fromImport,
            importAs,
            isNone,
            isNot,
            args,
            withAs,
            sequentialVariableNaming,
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
        const startTime = performance.now()
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
        console.log(`Rule-based prediction took ${performance.now() - startTime}`)
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
