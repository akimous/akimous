const assert = require('assert')
const Helper = codeceptjs.helper
const SPECIAL_KEYS = new Set(['Enter', 'Space', 'Tab', 'Escape'])
const META = (process.platform === 'darwin') ? 'Meta' : 'Control'

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
        if (!Array.isArray(input)) {
            assert(false, 'Only array is supported for type()')
        }
        await this.waitForFrames(1)
        for (const i of input) {
            await keyboard.down(i)
        }
        for (const i of input.reverse()) {
            await keyboard.up(i)
        }
        await this.waitForFrames(1)
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
    
    async setDoc(content) {
        const page = this.helpers['Puppeteer'].page
        return await page.evaluate(function(content) {
            window.g.activeEditor.cm.setValue(content)
        }, content)
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
        
    async disableRealtimeFormatter() {
        const page = this.helpers['Puppeteer'].page
        return await page.evaluate(function() {
            window.g.config.formatter.realtime = false
        })
    }
        
    async typeAndCompare(inputs, displays) {
        const page = this.helpers['Puppeteer'].page
        const { keyboard } = page
        const delay = { delay: 50 }
        for (const i of inputs) {
            let first = true
            if (Array.isArray(i)) {
                await this.type(i)
            } else if (SPECIAL_KEYS.has(i)) {
                await this.waitForCompletionOrContinueIn(.3)
                await keyboard.press(i, delay)
            } else {
                for (const j of i) {
                    if (!/[0-9a-zA-Z]/.test(j)){
                        if (j === ' ')
                            await this.waitForCompletionOrContinueIn(.5)
                        await keyboard.press(j, delay)
                        if (/[\s"(),[\]{}]/.test(j))
                            continue
                        await this.waitForCompletionOrContinueIn(.5)
                    } else if (first) {
                        await keyboard.press(j)
                        await this.waitForCompletionOrContinueIn(.5)
                        first = false
                    } else {
                        await keyboard.press(j, delay)
                    }
                }
            }
        }
        if (!displays) return
        const doc = await this.getDoc()
        for (const i of displays) {
            assert(doc.includes(i), `Not found: ${i}\nActual:\n${doc}`)
        }
    }
    
    async clear() {
        await this.type(['Escape'])
        await this.type([META, 'a'])
        await this.type(['Backspace'])
    }
}

module.exports = Editor
