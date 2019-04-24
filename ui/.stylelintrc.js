module.exports = {
    extends: "stylelint-config-recommended",
    rules: {
        "value-no-vendor-prefix": true,
        "property-no-vendor-prefix": true,
        "at-rule-no-vendor-prefix": true,
        "selector-pseudo-class-no-unknown": [
            true,
            { ignorePseudoClasses: ["global"] }
        ]
    },
    ignoreFiles: [
        "src/lib/doc-style-dark.css",
        "src/lib/guzzle.css",
        "src/EmptyComponent.html",
        "src/lib/Button.html", // svelte causing CssSyntaxError
    ],
}
