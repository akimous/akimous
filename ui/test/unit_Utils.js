import { highlightAllOccurrences } from '../src/lib/Utils'
import assert from 'assert'

describe('highlightAllOccurrences', function () {
    it('highlights', function () {
        assert.strictEqual(highlightAllOccurrences('a', ['a']), '<em>a</em>')
        assert.strictEqual(highlightAllOccurrences('A', ['a']), '<em>A</em>')
        assert.strictEqual(highlightAllOccurrences('abc', ['abc']), '<em>abc</em>')
        assert.strictEqual(highlightAllOccurrences('import', ['im']), '<em>im</em>port')
        assert.strictEqual(highlightAllOccurrences('AbcBbcCbc', ['abc']), '<em>Abc</em>BbcCbc')
        assert.strictEqual(highlightAllOccurrences('pypy', ['py']), '<em>pypy</em>')
        assert.strictEqual(highlightAllOccurrences('abac', ['a', 'c']), '<em>a</em>b<em>ac</em>')
        assert.strictEqual(highlightAllOccurrences('abac', ['a', 'ac']), '<em>a</em>b<em>ac</em>')
        assert.strictEqual(highlightAllOccurrences('abac', ['b']), 'a<em>b</em>ac')
        assert.strictEqual(highlightAllOccurrences('abac', ['ba']), 'a<em>ba</em>c')
        assert.strictEqual(highlightAllOccurrences('abac', ['ddd', 'eee']), 'abac')
        assert.strictEqual(highlightAllOccurrences('abac', []), 'abac')
    })
})
