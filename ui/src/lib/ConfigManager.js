import g from './Globals'

const config = {}
const projectConfig = {}
g.config = config
g.projectConfig = projectConfig

function setConfig(section, content) {
    Object.assign(config[section], content)
    g.masterSocket.send('SetConfig', {
        [section]: content
    })
}

function setProjectConfig(section, content) {
    Object.assign(projectConfig[section], content)
    g.masterSocket.send('SetProjectConfig', {
        [section]: content
    })
}

export { config, projectConfig, setConfig, setProjectConfig }
