module.exports = {
    plugins: [
        'codeceptjs',
    ],
    env: {
        'codeceptjs/codeceptjs': true
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
                    'jupyter',
                    'popup',
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
