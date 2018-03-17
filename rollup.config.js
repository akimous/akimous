import svelte from 'rollup-plugin-svelte'
import resolve from 'rollup-plugin-node-resolve'
import commonjs from 'rollup-plugin-commonjs'
import babel from 'rollup-plugin-babel'
//import strip from 'rollup-plugin-strip'
import sizes from 'rollup-plugin-sizes'
import postcss from 'rollup-plugin-postcss'

const production = !process.env.ROLLUP_WATCH

export default {
    input: 'src/main.js',
    output: {
        sourcemap: !production, // enable sourcemap when not in production
        format: 'iife',
        name: 'app',
        file: 'dist/bundle.js'
    },
    plugins: [
        svelte({
            dev: !production, // enable run-time checks when not in production
            // css: css => {
            //     css.write('dist/bundle.css', !production) // enable sourcemap when not in production
            // },
            cascade: true
        }),

        resolve(),
        commonjs(),
        postcss({
            plugins: [],
            minimize: production,
            // extract: 'dist/vendor.css'
        }),
        production && babel(),
        // production && strip(),  // this can break xterm
        production && sizes()
    ]
}
