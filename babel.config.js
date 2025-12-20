module.exports = {
  presets: [
    ['@babel/preset-env', {targets: {node: 'current'}}],
    '@babel/preset-typescript',
    '@babel/preset-react'
  ],
  plugins: [
    "@babel/plugin-transform-runtime",
    "@babel/plugin-syntax-jsx",
    "@babel/plugin-proposal-class-properties",
    "@babel/plugin-transform-modules-commonjs"
  ]
};
