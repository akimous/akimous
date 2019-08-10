import msgpack from 'msgpack-lite/dist/msgpack.min'
import g from './Globals'

// For performance's sake, expand it as function. About 6.5X faster than array mapping
const rowPreprocessors = {
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

g.rowProcessors = rowPreprocessors

class Socket {
    constructor(onopen) {
        this.webSocket = new WebSocket(`ws://${location.host}/ws/`)
        this.webSocket.binaryType = 'arraybuffer'
        this.webSocket.onopen = onopen
        this.webSocket.onclose = () => {
            if (!g.app) return
            g.app.$destroy()
            g.app = null
        }
        this.webSocket.onerror = event => {
            console.error(`Received error from ${this.path}: ${event}`)
        }

        this.sessions = {} // this.sessions[sessionId] = session
        this.maxSessionId = 1 // 0 is preserved for socket control

        this.webSocket.onmessage = event => {
            const [sessionId, eventName, object] = msgpack.decode(new Uint8Array(event.data)) // event.data is an ArrayBuffer
            // console.debug(`Received message from ${sessionId}: ${eventName}`, object)
            const preprocessor = rowPreprocessors[eventName]
            if (preprocessor && object.result) {
                object.result = object.result.map(preprocessor)
            }
            console.debug(`Preprocessed ${sessionId}/${eventName}`, object)
            const session = this.sessions[sessionId]
            if (!session) {
                console.error(`Session ${sessionId} does not exist`)
                return
            }
            const handler = session.handlers[eventName]
            if (!handler) {
                console.warn('Unhandled event', eventName)
                return
            }
            handler(object, eventName)
        }
    }

    createSession(endpoint, firstMessage) {
        const { sessions, webSocket } = this
        const sessionId = this.maxSessionId++
        const session = {
            _sessionId: sessionId,
            handlers: {},
            send(event, object) {
                console.debug(`Sending message from ${endpoint}, event ${event}:`, object)
                webSocket.send(msgpack.encode([sessionId, event, object]))
            },
            close() {
                webSocket.send(msgpack.encode([0, 'CloseSession', sessionId]))
                delete sessions[sessionId]
            }
        }
        this.sessions[sessionId] = session
        webSocket.send(msgpack.encode([0, 'OpenSession', { sessionId, endpoint, firstMessage }]))
        return session
    }

}

export { Socket }
