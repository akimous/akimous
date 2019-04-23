import { config, projectConfig } from './lib/ConfigManager'
import { Socket } from './lib/Socket'
import g from './lib/Globals'
import App from './App.html'
import './lib/common.css'
import './lib/doc-style-dark.css'
import 'normalize.css/normalize.css'
import 'codemirror/lib/codemirror.css'
import 'codemirror/addon/fold/foldgutter.css'
import 'xterm/dist/xterm.css'
import 'devicon/devicon.min.css'
import 'devicon/devicon-colors.css'

let app
const start = performance.now()
g.projectRoot = ['.']
g.ready = false

const socket = new Socket(() => {
    const session = socket.createSession('master')
    g.masterSession = session // TODO: get rid of this
    const { handlers } = session
    handlers['Connected'] = data => {
        g.sep = data.sep
        Object.assign(config, data.config)
        console.debug('first round-trip', performance.now() - start)
        app = new App({
            target: document.body,
        })
    }
    handlers['ProjectOpened'] = data => {
        g.projectRoot = data.root
        Object.assign(projectConfig, data.projectConfig)
        g.runConfiguration.set(g.projectConfig.runConfiguration)
    }
    session.send('OpenProject', { path: g.projectRoot })
})
g.socket = socket

export default app
