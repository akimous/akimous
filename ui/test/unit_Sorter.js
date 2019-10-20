import Sorter from '../src/editor/completion/Sorter.js'
import assert from 'assert'

describe('Sorter', function () {
    const sorter = new Sorter()

    function score(target, input) {
        sorter.setInput(input)
        return sorter.score(target)
    }

    it('scores', function () {
        assert(score('abc', 'abc') === 1000)
        assert(score('abc', 'abc') > score('ABC', 'abc'))
        assert(score('a', 'a') > score('A', 'a'))
        assert(score('A', 'A') > score('A', 'a'))
        assert(score('AbcBbcCbc', 'abc') > 0)
        assert(score('AbcBbcCbc', 'abc') === score('AbBbCb', 'abc'))
        assert(score('abc', 'abc') > score('AaBbCc', 'abc'))
        assert(score('AaBbCc', 'abc') > score('AaXbCc', 'abc'))
        assert(score('AaBbXx', 'abc') > score('AaYyXx', 'abc'))
    })
    
    function highlight(target, input) {
        sorter.setInput(input)
        sorter.score(target)
        return sorter.highlight()
    }
    
    it('highlights', function () {
        assert.strictEqual(highlight('a', 'a'), '<em>a</em>')
        assert.strictEqual(highlight('A', 'a'), '<em>A</em>')
        assert.strictEqual(highlight('abc', 'abc'), '<em>abc</em>')
        assert.strictEqual(highlight('import', 'im'), '<em>im</em>port')
        assert.strictEqual(highlight('AbcBbcCbc', 'abc'), '<em>A</em>bc<em>B</em>bc<em>C</em>bc')
        assert.strictEqual(highlight('AbcBbcCbc', 'abcc'), '<em>A</em>bc<em>B</em>bc<em>C</em>b<em>c</em>')
        assert.strictEqual(highlight('_a_dog', '_adog'), '<em>_a</em>_<em>dog</em>')
    })
})
