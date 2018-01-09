class Sorter {
    constructor() {
        this.DP_SIZE = 32
        this.m = new Array(this.DP_SIZE)
        for (let i = 0; i < this.DP_SIZE; i++)
            this.m[i] = new Array(this.DP_SIZE).fill(0)
    }
    setInput(text) {
        this.input = text
        this.inputUpper = text.toUpperCase()
    }
    highlight() {
        const MIN = -9999,
            target = this.target,
            input = this.input,
            inputUpper = this.inputUpper,
            targetUpper = this.targetUpper,
            inputLength = input.length > this.DP_SIZE - 1 ? this.DP_SIZE - 1 : input.length,
            targetLength = target.length,
            m = this.m,
            trace = []
        if (input === target) return `<em>${target}</em>`
        let i = inputLength, // row
            j = targetLength - 1 // column
        while (i >= 0 && j >= 0) {
            let deltaLeft = undefined,
                goUp = false
            const charIndex = i + j - 1
            if (charIndex < 0) {
                break
            } else if (i <= 0) {
                goUp = false
            } else if (j <= 0) {
                goUp = true
            } else {
                const current = m[i][j]
                const up = m[i - 1][j]
                const left = m[i][j - 1]
                const deltaUp = current - up
                deltaLeft = left === MIN ? MIN : current - left
                goUp = deltaUp > deltaLeft // determine should go up or left
                // exceptions
                if (targetUpper[charIndex] !== inputUpper[i - 1]) {
                    goUp = false // unmatched
                } else if (goUp) {
                    const leftUp = m[i - 1][j - 1]
                    const deltaNextUp = left - leftUp
                    if (deltaUp <= deltaNextUp && left !== MIN)
                        goUp = false // if left hand side has greater delta, go left instead of go up
                }
            }
            // at boundary, can only go up or left
            if (j == 0) goUp = true
            else if (i == 0) goUp = false

            if (deltaLeft === MIN && charIndex < targetLength && targetUpper[charIndex] !== inputUpper[i - 1]) {
                i-- // force go up if it is an unmatched character, no highlight
            } else if (goUp) {
                // only highlight those actually match
                if (charIndex < targetLength && targetUpper[charIndex] === inputUpper[i - 1])
                    trace.push(i + j - 1)
                i--
            } else { // go left (skip)
                j--
            }
        }
        // generate highlighted string
        let result = [],
            t = 0, // target index
            p = trace.length - 1, // trace index
            open = false
        while (t < targetLength) {
            const tp = trace[p]
            if (tp === t && !open) {
                result.push('<em>')
                open = true
            } else if (tp !== t && open) {
                result.push('</em>')
                open = false
            }
            tp === t && --p
            result.push(target[t++])
        }
        if (open) result.push('</em>')
        return result.join('')
    }

    score(target) {
        const input = this.input,
            inputUpper = this.inputUpper,
            targetUpper = target.toUpperCase(),
            isAllUpper = (target === targetUpper),
            targetLength = target.length,
            inputLength = input.length > this.DP_SIZE - 1 ? this.DP_SIZE - 1 : input.length,
            m = this.m

        const MATCH_LOWER = 5,
            MATCH_UPPER = 10,
            SKIP = -1,
            UNMATCHED = -50,
            MIN = -9999
        this.target = target
        this.targetUpper = targetUpper

        if (input === target) return 1000

        // initialize
        for (let i = 0; i <= inputLength; i++)
            m[i].fill(0, 0, targetLength)

        // first row
        m[0].fill(-1, 1, targetLength)

        // second row and beyond
        for (let i = 1; i <= inputLength; i++) {
            // first column
            let firstColumnScore = MIN
            if (i === 1 && inputUpper[0] === targetUpper[0]) {
                firstColumnScore = MATCH_UPPER
            } else if (inputUpper[i - 1] === target[i - 1]) {
                if (isAllUpper && target[i - 2] !== '_') firstColumnScore = MATCH_LOWER
                else firstColumnScore = MATCH_UPPER
            } else if (inputUpper[i - 1] === targetUpper[i - 1]) {
                if (target[i - 2] === '_') firstColumnScore = MATCH_UPPER
                else firstColumnScore = MATCH_LOWER
            }
            m[i][0] = firstColumnScore === MIN ? MIN : (m[i - 1][0] + firstColumnScore)

            // second column and beyond
            let skipped = false
            for (let j = 1; j < targetLength; j++) {
                let scoreFromTop = m[i - 1][j]
                if (scoreFromTop === MIN) {
                    // do nothing
                } else if (i + j - 1 >= targetLength) {
                    scoreFromTop += UNMATCHED
                } else if (inputUpper[i - 1] === target[i + j - 1]) {
                    if (isAllUpper && target[i + j - 2] !== '_') scoreFromTop += MATCH_LOWER
                    else scoreFromTop += MATCH_UPPER
                } else if (inputUpper[i - 1] === targetUpper[i + j - 1]) {
                    if (target[i + j - 2] === '_') scoreFromTop += MATCH_UPPER
                    else scoreFromTop += MATCH_LOWER
                } else scoreFromTop = MIN

                let scoreFromLeft = m[i][j - 1]
                if (scoreFromLeft === MIN) scoreFromLeft = MIN
                else if (!skipped) {
                    scoreFromLeft += SKIP
                }
                if (scoreFromTop > scoreFromLeft) {
                    skipped = false
                    m[i][j] = scoreFromTop
                } else {
                    skipped = true
                    m[i][j] = scoreFromLeft
                }
            }
        }
        return m[inputLength][targetLength - 1]
    }
}

export default Sorter
