import msgpack from 'msgpack-lite/dist/msgpack.min'
import g from './Globals'

// For performance's sake, expand it as function. About 6.5X faster than array mapping
const rowPreprocessor = {
    Prediction([text, type, score]) {
        return { text, type, score }
    },
    ExtraPrediction([text, type, score]) {
        return { text, type, score }
    },
    RealTimeLints([message, line, ch]) {
        return { message, line, ch }
    },
    SpellingErrors([line, ch, token, highlight]) {
        return { line, ch, token, highlight }
    },
    FoundInDirectory([file, matches]) {
        return { file, matches }
    }
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
        return this
    }
    
    close() {
        this.socket.onclose = () => {}
        this.socket.close()
    }

    send(event, obj) {
        console.debug(`Sending message from ${this.path}, event ${event}:`, obj)
        this.socket.send(msgpack.encode([event, obj]))
    }
}

export { Socket, rowPreprocessor }
