import svelte from 'rollup-plugin-svelte'
import resolve from 'rollup-plugin-node-resolve'
import commonjs from 'rollup-plugin-commonjs'
import babel from 'rollup-plugin-babel'

const production = !process.env.ROLLUP_WATCH

export default {
    input: 'src/main.js',
    output: {
        sourcemap: !production, // enable sourcemap when in production
        format: 'iife',
        name: 'app',
        file: 'build/bundle.js'
    },

    plugins: [
        svelte({
            dev: !production, // enable run-time checks when not in production
            css: css => {
                css.write('build/bundle.css', !production) // enable sourcemap when in production
            },
            cascade: true
        }),

        resolve(),
        commonjs({
            namedExports: {}
        }),
        
        production && babel()
    ]
}