exports.config = {
    tests: './test/*_test.js',
    output: './testOutput',
    helpers: {
        Puppeteer: {
            url: 'http://localhost:3179',
            show: true,
            restart: false,
            keepBrowserState: true,
            chrome: {
                devtools: true
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
