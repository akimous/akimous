exports.config = {
    tests: './test/*_test.js',
    output: './testOutput',
    helpers: {
        Puppeteer: {
            url: 'http://localhost:3178',
            show: false,
            restart: false,
            keepBrowserState: true,
            windowSize: '1280x800',
            waitForAction: 128,
            chrome: {
                devtools: false
            }
        },
        Editor: {
            require: './test/editor_helper.js',
        }
    },
    include: {
        I: './test/steps_file.js'
    },
    bootstrap: null,
    mocha: {},
    name: 'ui'
}
