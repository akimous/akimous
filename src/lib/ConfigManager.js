import { Socket } from './Socket'
import g from './Globals'

const config = {}
g.config = config

let startupCallback

const socket = new Socket('ws://127.0.0.1:3179/config')
    .addHandler('Config', data => {
        console.warn(data)
        Object.assign(config, data)
        if (startupCallback) {
            startupCallback()
            startupCallback = null
        }
    })

function connect(callback) {
    startupCallback = callback
    socket.connect(() => {
        socket.send('get', null)
    })
}

function setConfig(section, content) {
    Object.assign(config[section], content)
    socket.send('set', {
        [section]: content
    })
}

export { config, connect, setConfig }
