import g from './Globals'

const config = {}
const projectState = {}
g.config = config
g.projectState = projectState

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

function setProjectState(section, content) {
    const original = projectState[section]
    if (!isDirty(original, content)) return
    Object.assign(original, content)
    g.projectSession.send('SetProjectState', {
        [section]: content
    })
}

export { config, projectState, setConfig, setProjectState }
