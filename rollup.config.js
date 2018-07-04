import svelte from 'rollup-plugin-svelte'
import resolve from 'rollup-plugin-node-resolve'
import commonjs from 'rollup-plugin-commonjs'
import babel from 'rollup-plugin-babel'
//import sizes from 'rollup-plugin-sizes'
import postcss from 'rollup-plugin-postcss'
import progress from 'rollup-plugin-progress'
import autoprefixer from 'autoprefixer'

const production = !process.env.ROLLUP_WATCH

export default {
    input: 'src/main.js',
    output: {
        sourcemap: !production, // enable sourcemap when not in production
        format: 'iife',
        name: 'app',
        file: 'dist/bundle.js'
    },
    perf: false,
    plugins: [
        svelte({
            dev: !production, // enable run-time checks when not in production
        }),

        resolve(),
        commonjs(),
        postcss({
            plugins: [autoprefixer()], // not effective for svelte component
            minimize: true,
            sourcemap: !production,
            // extract: 'dist/bundle.css'
        }),
        production && progress(),
        // NOTE: be careful that babel-plugin-transform-merge-sibling-variables 
        // is breaking codemirror code folding, should be disabled in .babelrc (mergeVars)
        production && babel(),
        
        // Causing TypeError: details.bundle.modules.forEach is not a function
        // production && sizes(),
    ]
}
