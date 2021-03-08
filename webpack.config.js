const path = require('path')
const CKEditorWebpackPlugin = require( '@ckeditor/ckeditor5-dev-webpack-plugin' );
const { styles } = require( '@ckeditor/ckeditor5-dev-utils' );

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
            },
            {
                test: /ckeditor5-[^/\\]+[/\\]theme[/\\].+\.css$/,
                use: [
                    {
                        loader: 'style-loader',
                        options: {
                            injectType: 'singletonStyleTag',
                            attributes: {
                                'data-cke': true
                            }
                        }
                    },
                    {
                        loader: 'css-loader',
                    },
                    {
                        loader: 'postcss-loader',
                        options: {
                            postcssOptions: styles.getPostCssConfig( {
                                themeImporter: {
                                    themePath: require.resolve( '@ckeditor/ckeditor5-theme-lark' )
                                },
                                // minify: true
                            })
                        }
                    },
                ]
            },
            {
                test: /\.(css)$/,
                exclude: [
                    /ckeditor5-[^/\\]+[/\\]theme[/\\].+\.css$/,
                ],
                use: [
                    'style-loader',
                    'css-loader',
                ]
            },
            {
                test: /\.(jpg|jpeg|gif|png)$/,
                use: {
                    loader: 'file-loader',
                    options: {
                        name: '[name].[ext]',
                        publicPath: 'images',
                        outputPath: 'images',
                    }
                }
            },
            {
                test: /\.(eot|ttf|woff|woff2)$/,
                use: {
                    loader: 'file-loader',
                    options: {
                        name: '[name].[ext]',
                        publicPath: 'fonts',
                        outputPath: 'fonts',
                    }
                }
            },
            {
                test: /ckeditor5-[^/\\]+[/\\]theme[/\\]icons[/\\][^/\\]+\.svg$/,
                use: [ 'raw-loader' ]
            },
            {
                test: /\.(otf|ttf|eot|svg|woff(2)?)(\?[a-z0-9=&.]+)?$/,
                exclude: [
                    /ckeditor5-[^/\\]+[/\\]theme[/\\]icons[/\\][^/\\]+\.svg$/,
                    /ckeditor5-[^/\\]+[/\\]theme[/\\].+\.css/,
                ],
                use: {
                    loader: 'url-loader',
                }
            },
        ]
    },
}