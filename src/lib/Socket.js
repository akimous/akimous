import msgpack from 'msgpack-lite/dist/msgpack.min'

// For performance's sake, expand it as function. About 6.5X faster than array mapping
const rowPreprocessor = {
    Prediction(tuple) {
        return {
            c: tuple[0],
            t: tuple[1],
            s: tuple[2],
        }
    },
    ExtraPrediction(tuple) {
        return {
            c: tuple[0],
            t: tuple[1],
            s: tuple[2],
        }
    },
}

class Socket {
    constructor(path) {
        this.path = path
        this.handlers = {}
    }

    addHandler(event, handler) {
        this.handlers[event] = handler
        return this
    }

    connect(callback) {
        this.socket = new WebSocket(this.path)
        this.socket.binaryType = 'arraybuffer'
        this.socket.onopen = callback
        this.socket.onclose = () => {
            setTimeout(() => {
                this.connect(callback)
            }, 3000)
        }
        this.socket.onerror = event => {
            console.error(`Recieved error from ${this.path}: ${event}`)
        }
        this.socket.onmessage = event => {
            const [e, obj] = msgpack.decode(new Uint8Array(event.data)) // event.data is ArrayBuffer
            console.debug(`Recieved message from ${this.path}: ${e}`, obj)
            const preprocessor = rowPreprocessor[e]
            if (preprocessor && obj.result) {
                obj.result = obj.result.map(preprocessor)
            }
            // console.debug(`Preprocessed ${e}`, obj)
            const handler = this.handlers[e]
            if (!handler) {
                console.warn('Unhandled event', e)
                return
            }
            handler(obj, e)
        }
        return this
    }

    send(event, obj) {
        console.debug(`Sending message from ${this.path}, event ${event}:`, obj)
        this.socket.send(msgpack.encode([event, obj]))
    }
}

export { Socket, rowPreprocessor }
