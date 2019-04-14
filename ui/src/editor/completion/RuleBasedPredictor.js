import { highlightSequentially, inSomething } from '../../lib/Utils'
import { scanInSameLevelOfBraces } from '../EditorFunctions'
import snakecase from 'lodash.snakecase'
import pluralize from 'pluralize'

const RIGHT_HALVES = new Set([',', ')', ']', '}'])
const MAX_SCAN_LINES = 100
const FULL_STATEMENT_COMPLETION_CONSISTENCY_CHECKS = [
    /\s*for\s/,
    /\s*def\s/,
    /\s*class\s/,
    /\s*with\s/,
]


function fullStatementCompletion({ topHit, cm, line, lineContent }) {
    if (!topHit) return

    const topHitCompletion = topHit.text
    const lineCount = cm.lineCount()
    let lineUp = line - 1
    let lineDown = line + 1
    let sourceLine = -1
    let sourceLineContent = ''
    let index = -1
    
    const targetLineConsistencyCheckResults = FULL_STATEMENT_COMPLETION_CONSISTENCY_CHECKS.map(check => {
        return check.test(lineContent)
    })
    
    const containsTopHit = l => {
        sourceLineContent = cm.getLine(l)
        index = sourceLineContent.indexOf(topHitCompletion)
        if (index < 0) return false
        
        const commentStart = sourceLineContent.indexOf('#')
        if (commentStart > 0 && index > commentStart) return false
        
        // previous character is alphanumeric
        if (index > 0 && /\w|\d/.test(sourceLineContent.charAt(index - 1))) return false
        
        if (/\s*import\s/.test(sourceLineContent)) return false
        
        for (let i = 0; i < FULL_STATEMENT_COMPLETION_CONSISTENCY_CHECKS.length; i++) {
            if (FULL_STATEMENT_COMPLETION_CONSISTENCY_CHECKS[i].test(sourceLineContent) ^
                targetLineConsistencyCheckResults[i]) return false
        }
        
        sourceLine = l
        return true
    }

    let scannedCount = 0
    // find the nearest line including topHit.text
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
        line: sourceLine,
        ch: index
    }, (cm, char, pos) => {
        if (pos.line !== sourceLine)
            return sourceLineContent.length
        if (RIGHT_HALVES.has(char))
            return pos.ch
    }, 1)

    if (result)
        return sourceLineContent.substring(index, result)
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
    result = result[topHit.text]
    if (!result) return
    return topHit.text + result
}

function fromImport({ lineContent, topHit }) {
    if (!topHit) return
    if (topHit.type !== 'module') return
    if (!/^\s*from/.test(lineContent)) return
    if (/\simport\s/.test(lineContent)) return
    return topHit.text + ' import '
}

function importAs({ lineContent, topHit }) {
    if (!topHit) return
    if (!/import/.test(lineContent)) return
    if (/\sas\s/.test(lineContent)) return
    return topHit.text + ' as '
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
    if (topHit.text !== 'as') return
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
    if (topHit.type !== 'statement') return
    const lastLine = cm.getLine(line - 1)
    const index = lastLine.indexOf(topHit.text)
    if (index === -1) return
    if (index + topHit.text.length + 3 >= lastLine.length) return
    const charsAfterTopHitInLastLine = lastLine.substr(index + topHit.text.length, 3)
    if (charsAfterTopHitInLastLine !== ' = ') return
    const result = nextPossibleVariableName(topHit.text)
    if (!result) return
    if (completions.some(i => i.text === result)) return
    return result + ' = '
}

function forElementInCollection({ topHit, lineContent }) {
    if (!topHit) return
    if (!/^\s*for\s/.test(lineContent)) return
    if (pluralize.isPlural(topHit.text)) {
        const singular = pluralize.singular(topHit.text)
        if (singular !== topHit.text) return `${singular} in ${topHit.text}`
    }
}

class RuleBasedPredictor {
    constructor(context) {
        this.context = context
        this.predictors = [
            fullStatementCompletion,
            fixedPredictionForImport,
            fromImport,
            importAs,
            isNone,
            isNot,
            args,
            withAs,
            sequentialVariableNaming,
            forElementInCollection,
        ]
    }

    predict(context) {
        context = Object.assign(this.context, context)
        const { input } = context

        context.lineContent = context.cm.getLine(context.line)

        let result = []
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
        
        // deduplicate and order by length
        result = [...new Set(result)].sort((a, b) => a.length - b.length)
        
        console.log(`Rule-based prediction took ${performance.now() - startTime}`)
        return result.map(text => {
            return {
                text,
                type: 'full-statement',
                score: 0,
                sortScore: 0,
                highlight: highlightSequentially(text, input)
            }
        })
    }

}

export default RuleBasedPredictor
