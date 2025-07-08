// react/webpack.config.js
const path = require('path');
const fs = require('fs');
const glob = require('glob');
const webpack = require('webpack');

// Base configuration
const baseConfig = {
    mode: 'development',
    devtool: 'source-map',
    module: {
        rules: [
            {
                test: /\.jsx?$/,
                exclude: /node_modules/,
                use: {
                    loader: 'babel-loader',
                    options: {
                        presets: ['@babel/preset-env', '@babel/preset-react']
                    }
                }
            },
            {
                test: /\.css$/,
                use: ['style-loader', 'css-loader']
            }
        ]
    },
    resolve: {
        extensions: ['.js', '.jsx'],
        alias: {
            '@': path.resolve(__dirname, 'src')
        }
    }
};

// Main app configuration
const mainConfig = {
    ...baseConfig,
    name: 'main',
    entry: {
        main: './src/index.js'
    },
    output: {
        path: path.resolve(__dirname, '../app/static/js'),
        filename: '[name].bundle.js',
        chunkFilename: '[name].chunk.js',
        publicPath: '/static/js/'
    },
    optimization: {
        minimize: false,
        usedExports: false,
        concatenateModules: false,
        sideEffects: false,
        splitChunks: {
            chunks: 'initial',
            cacheGroups: {
                vendor: {
                    test: /[\\/]node_modules[\\/]/,
                    name: 'vendor',
                    chunks: 'initial'
                }
            }
        }
    }
};

// User components configuration
const userComponentConfigs = [];

// Find all user components
const user_component_files = glob.sync('./src/user_components/*.js');

user_component_files.forEach(file => {
    const component_name = path.basename(file, '.js');
    const entry_path = file.startsWith('./') ? file : `./${file}`;
    
    userComponentConfigs.push({
        ...baseConfig,
        name: `user_component_${component_name}`,
        entry: entry_path,
        output: {
            path: path.resolve(__dirname, '../app/static/js/user_components'),
            filename: `${component_name}.bundle.js`,
            publicPath: '/static/js/',
            library: `components/${component_name}`,
            libraryTarget: 'window',
            libraryExport: 'default'
        },
        externals: {
            'react': 'React',
            'react-dom': 'ReactDOM',
            // Add pattern matching for components
            ...Object.fromEntries(
                glob.sync('./src/components/*.js').map(compFile => {
                    const compName = path.basename(compFile, '.js');
                    return [
                        `../components/${compName}`,
                        `window.Components.${compName}`
                    ];
                })
            )
        },
        optimization: {
            minimize: false,
            // Disable all splitting for user components
            splitChunks: false,
            runtimeChunk: false
        },
        plugins: [
            new webpack.BannerPlugin({
                banner: `// Ensure window.Components exists
window.Components = window.Components || {};`,
                raw: true
            })
        ]
    });
});

// Export array of configurations
module.exports = [mainConfig, ...userComponentConfigs];

console.log(`Building main app and ${userComponentConfigs.length} user components`);