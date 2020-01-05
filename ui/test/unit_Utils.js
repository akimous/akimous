import { highlightAllOccurrences } from '../src/lib/Utils'
import assert from 'assert'

describe('highlightAllOccurrences', function () {
    it('highlights', function () {
        const t = (target, keywords, highlighted) => {
            assert.strictEqual(highlightAllOccurrences(target, keywords).display, highlighted)
        }
        t('a', ['a'], '<em>a</em>')
        t('A', ['a'], '<em>A</em>')
        t('abc', ['abc'], '<em>abc</em>')
        t('import', ['im'], '<em>im</em>port')
        t('AbcBbcCbc', ['abc'], '<em>Abc</em>BbcCbc')
        t('pypy', ['py'], '<em>pypy</em>')
        t('abac', ['a', 'c'], '<em>a</em>b<em>ac</em>')
        t('abac', ['a', 'ac'], '<em>a</em>b<em>ac</em>')
        t('abac', ['b'], 'a<em>b</em>ac')
        t('abac', ['ba'], 'a<em>ba</em>c')
        t('abac', ['ddd', 'eee'], 'abac')
        t('abac', [], 'abac')
        t('abac', ['c', ''], 'aba<em>c</em>') // shouldn't be infinite loop
    })
})
