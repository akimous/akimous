import keyboardJS from 'keyboardjs'
import g from './Globals'

function hotkey(key, handler) {
    keyboardJS.bind(key, e => {
        e.preventDefault()
        return handler(e)
    })
}

hotkey('mod + s', g.saveFile)

hotkey('mod + shift + s', e => {
    g.saveAll()
})

export default {}