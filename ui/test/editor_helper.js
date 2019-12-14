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

    async waitForCompletionOrContinueIn(timeout = 1.) {
        const page = this.helpers['Puppeteer'].page
        try {
            await page.waitForSelector('.completion', {
                visible: true,
                timeout: timeout * 1000
            })
        } catch {
            // do nothing
        }
    }
    
    async waitForFrames(n) {
        const page = this.helpers['Puppeteer'].page
        return await page.evaluate(function(counter) {
            return new Promise(function(resolve) {
                function count() {
                    counter -= 1
                    if (counter > 0) {
                        requestAnimationFrame(count)
                    } else {
                        resolve(true)
                    }
                }
                setTimeout(count, 1)
            })
        }, n)
    }
            
    async getDoc() {
        const page = this.helpers['Puppeteer'].page
        return await page.evaluate(function() {
            return new Promise(function(resolve) {
                requestAnimationFrame(function() {
                    requestAnimationFrame(function() {
                        resolve(window.g.activeEditor.cm.getValue())
                    })
                })
            })
        })
    }
}

module.exports = Editor
