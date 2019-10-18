const Helper = codeceptjs.helper

class Editor extends Helper {

    // before/after hooks
    _before() {
        // remove if not used
    }

    _after() {
        // remove if not used
    }

    // add custom methods here
    // If you need to access other helpers
    // use: this.helpers['helperName']
    async type(input) {
        const page = this.helpers['Puppeteer'].page
        const { keyboard } = page
        if (Array.isArray(input)) {
            for (const i of input) {
                await keyboard.down(i)
            }
            for (const i of input.reverse()) {
                await keyboard.up(i)
            }
        }
    }

}

module.exports = Editor
