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
import 'primer-tooltips/build/build.css'
import 'devicon/devicon.min.css'
import 'devicon/devicon-colors.css'

let app
const start = performance.now()
g.projectRoot = ['.']
const socket = new Socket('')
    .addHandler('Connected', data => {
        g.clientId = data.clientId
        g.sep = data.sep
        Object.assign(config, data.config)
        console.debug('first round-trip', performance.now() - start)
        app = new App({
            target: document.body,
        })
    })
    .addHandler('ProjectOpened', data => {
        g.projectRoot = data.root
        Object.assign(projectConfig, data.projectConfig)
        g.runConfiguration.set(g.projectConfig.runConfiguration)
    })
    .connect(() => {
        console.info('Connected')
        socket.send('OpenProject', { path: g.projectRoot })
    })
g.masterSocket = socket

export default app
