module.exports = {
    plugins: [
        'codeceptjs',
    ],
    env: {
        'codeceptjs/codeceptjs': true
    },
    rules: {
        'spellcheck/spell-checker': [1,
            {
                comments: true,
                strings: true,
                identifiers: true,
                lang: 'en_US',
                skipWords: [
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
