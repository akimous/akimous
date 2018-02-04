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
            if (this.debug) console.log(`Recieved message from ${this.path}:`, msg)
            const handler = this.handlers[msg.cmd]
            if (handler != undefined)
                handler(msg)
        }
        
        this.socket.onerror = event => {
            console.log(`Recieved error from ${this.path}: ${event}`)
        }
        
        this.socket.onopen = () => {
            console.log(`WebSocket opened on ${this.path}`)
            if (callback != null)
                callback(this)
        }
        
        this.socket.onclose = () => {
            console.warn(`WebSocket unexpectedly dropped on ${this.path}`)
            // TODO: should show warning on UI
            setTimeout(() => {
                this.connect(callback)
            }, 3000)
        }
    }
    
    send(obj) {
        if (this.debug) console.log(`Sending message from ${this.path}:`, obj)
        this.socket.send(JSON.stringify(obj))
    }
    
    close() {
        this.socket.close()
        this.socket = undefined
    }
}