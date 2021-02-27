const path = require('path')

const jsOut = './web/dst/'
const jsIn = './web/src/js/'

module.exports = {
    entry: {
        auth: jsIn + 'auth.js',
        colorTheme: jsIn + 'colorTheme.js',
        editor: jsIn + 'editor.js',
        firebaseAuth: jsIn + 'firebaseAuth.js',
        home: jsIn + 'home.js',
        index: jsIn + 'index.js',
        'js.cookie.min': jsIn + 'js.cookie.min.js',
        loadCommonParts: jsIn + 'loadCommonParts.js',
        login: jsIn + 'login.js',
        registComplete: jsIn + 'registComplete.js',
        resetPassword: jsIn + 'resetPassword.js',
        sidebar: jsIn + 'sidebar.js',
        signup: jsIn + 'signup.js',
        tag: jsIn + 'tag.js',
        updateUserId: jsIn + 'updateUserId.js',
        userSettings: jsIn + 'userSettings.js',
    },
    output: {
        path: path.resolve(__dirname, jsOut + 'js'),
        filename: '[name].js'
    },
    plugins: [
    ],
    module: {
        rules: [
            {
                test: /\.js$/,
                use: {
                    loader: 'babel-loader',
                    options: {
                        babelrc: true,
                    }
                }
            }
        ]
    },
}