import g from './Globals'
export default class {
    constructor(path) {
        this.path = path
        this.debug = true
        this.handlers = {}
    }
    
    addHandler(command, handler) {
        this.handlers[command] = handler
    }
    
    connect(callback) {
        this.socket = new WebSocket(this.path)
        
        this.socket.onmessage = event => {
            const msg = JSON.parse(event.data)
            if (this.debug) console.debug(`Recieved message from ${this.path}:`, msg)
            const handler = this.handlers[msg.cmd]
            if (handler != undefined)
                handler(msg)
        }
        
        this.socket.onerror = event => {
            console.log(`Recieved error from ${this.path}: ${event}`)
        }
        
        this.socket.onopen = () => {
            // if (this.path.includes('fileTree'))
            //    g.notificationBar.show('success', 'Connected to Python agent')
            if (callback != null)
                callback(this)
        }
        
        this.socket.onclose = () => {
            if (this.path.includes('fileTree'))
                g.notificationBar.show('warning', 'Connection to Python agent unexpectedly dropped')
            setTimeout(() => {
                this.connect(callback)
            }, 3000)
        }
    }
    
    send(obj) {
        if (this.debug) console.debug(`Sending message from ${this.path}:`, obj)
        this.socket.send(JSON.stringify(obj))
    }
    
    close() {
        this.socket.close()
        this.socket = undefined
    }
}