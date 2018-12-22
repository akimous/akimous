import g from './Globals'

const config = {}
g.config = config

function setConfig(section, content) {
    Object.assign(config[section], content)
    g.masterSocket.send('SetConfig', {
        [section]: content
    })
}

export { config, setConfig }
