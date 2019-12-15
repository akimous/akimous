module.exports = {
    plugins: [
        'codeceptjs',
        'mocha',
    ],
    extends: [
        'plugin:mocha/recommended',
    ],
    env: {
        'codeceptjs/codeceptjs': true,
        'mocha': true,
    },
    globals: {
        codeceptjs: 'readonly',
    },
    rules: {
        'spellcheck/spell-checker': [1,
            {
                comments: true,
                strings: false,
                identifiers: true,
                lang: 'en_US',
                skipWords: [
                    'codeceptjs',
                    'dont',
                    'formatter',
                    'jupyter',
                    'popup',
                    'realtime',
                ],
                skipIfMatch: [
                    'http://[^s]*',
                    'https://[^s]*',
                ],
                skipWordIfMatch: [
                    'px'
                ],
                minLength: 3
            }
        ]
    },
}
