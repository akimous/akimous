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
    
    // use when I.click is not working for mysterious reasons
    async doubleClickAlt(text, selector) {
        const page = this.helpers['Puppeteer'].page
        const elements = await page.$$(selector)
        for (const element of elements) {
            if (await element.evaluate(node => node.innerText) === text) {
                await element.click({
                    clickCount: 2,
                    delay: .1,
                })
                return
            }
        }
        console.warn('Element not found', text, selector)
    }
    
}

module.exports = Editor
