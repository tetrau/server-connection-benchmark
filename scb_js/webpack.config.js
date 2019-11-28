module.exports = {
    mode: 'development',
    entry: './index.js',
    output: {
        filename: 'main.js',
        publicPath: 'dist'
    },
    module: {
        rules: [
            {
                test: /\.js$/,
                exclude: /node_modules/,
                loader: "babel-loader"
            }
        ]
    },
    devServer: {
        openPage: 'test/test.html',
        open: true
    }
};
