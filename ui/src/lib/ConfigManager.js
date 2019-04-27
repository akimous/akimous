import g from './Globals'

const config = {}
const projectConfig = {}
g.config = config
g.projectConfig = projectConfig

function isDirty(original, current) {
    for (let key in current) {
        if (original[key] !== current[key]) return true
    }
    return false
}

function setConfig(section, content) {
    const original = config[section]
    if (!isDirty(original, content)) return
    Object.assign(original, content)
    g.configSession.send('SetConfig', {
        [section]: content
    })
}

function setProjectConfig(section, content) {
    const original = projectConfig[section]
    if (!isDirty(original, content)) return
    Object.assign(original, content)
    g.projectSession.send('SetProjectConfig', {
        [section]: content
    })
}

export { config, projectConfig, setConfig, setProjectConfig }
