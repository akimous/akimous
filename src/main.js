import { connect } from './lib/ConfigManager'
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
connect(() => {
    console.debug('first round-trip', performance.now() - start)
    app = new App({
        target: document.body,
    })
})

export default app
