import { config, projectState } from './lib/ConfigManager'
import { Socket } from './lib/Socket'
import g from './lib/Globals'
import App from './App.html'
import './lib/doc-style-dark.css'
import 'normalize.css/normalize.css'
import 'codemirror/lib/codemirror.css'
import 'codemirror/addon/fold/foldgutter.css'
import 'xterm/css/xterm.css'
import 'devicon/devicon.min.css'
import 'devicon/devicon-colors.css'

let app
const start = performance.now()
g.projectRoot = '.'
g.ready = false

const socket = new Socket(() => {
    g.configSession = socket.createSession('config')
    g.projectSession = socket.createSession('project')

    g.configSession.handlers['Connected'] = data => {
        g.pathSeparator = data.pathSeparator
        Object.assign(config, data.config)
        console.debug('first round-trip', performance.now() - start)
        if (g.config.lastOpenedFolder) {
            g.projectSession.send('OpenProject', { path: g.config.lastOpenedFolder })
        } else {
            g.app = app = new App({
                target: document.body,
                props: {
                    initialized: false,
                    openFolder: true
                }
            })
        }
    }
    g.projectSession.handlers['ProjectOpened'] = data => {
        const { root } = data
        g.projectRoot = root
        g.ready = false
        g.focusStack = []
        Object.assign(projectState, data.projectState)

        if (app) app.$destroy()
        g.app = app = new App({
            target: document.body,
            props: {
                initialized: true,
            }
        })
        g.runConfiguration.$set(g.projectState.runConfiguration)
        document.title = `Akimous - ${root[root.length - 1]}`
    }
})
g.socket = socket

export default app
