const path = require('path');
const fs = require('fs');
const glob = require('glob');

// Function to get all component entries
function getComponentEntries() {
    const entries = {
        // Main app bundle
        main: './src/index.js'
    };

    // Find all components in the components directory (excluding standard ones)
    const component_files = glob.sync('./src/components/*.js', {
        ignore: [
            './src/components/DynamicPage.js',
            './src/components/LoadingScreen.js',
            './src/components/Login.js',
            './src/components/HtmlRenderer.js',
            './src/components/ComponentBuilder.js'
        ]
    });

    component_files.forEach(file => {
        const name = path.basename(file, '.js');
        // Ensure the path starts with ./
        const entry_path = file.startsWith('./') ? file : `./${file}`;
        entries[`components/${name}`] = entry_path;
    });

    // Find all components in the user_components directory
    const user_component_files = glob.sync('./src/user_components/*.js');
    
    user_component_files.forEach(file => {
        const name = path.basename(file, '.js');
        // Ensure the path starts with ./
        const entry_path = file.startsWith('./') ? file : `./${file}`;
        // You can choose to prefix these differently if you want
        entries[`user_components/${name}`] = entry_path;
    });

    console.log('Webpack entries:', entries);
    return entries;
}

module.exports = {
    mode: 'development', // Instead of 'production'
    
    optimization: {
        minimize: false,  // Disable minification
        usedExports: false,  // Keep all exports
        concatenateModules: false,  // Don't concatenate modules
        sideEffects: false  // Don't remove "unused" code
    },
    
    devtool: 'source-map', // Or 'inline-source-map' for inline maps
    
    entry: getComponentEntries(),
    output: {
        path: path.resolve(__dirname, '../app/static/js'),
        filename: '[name].bundle.js',
        chunkFilename: '[name].chunk.js',
        publicPath: '/static/js/',
        // For components, export them in a way we can access
        library: {
            name: '[name]',
            type: 'umd',
            export: 'default'
        }
    },
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
    },
    optimization: {
        splitChunks: {
            chunks: (chunk) => {
                // Don't split component chunks
                return chunk.name === 'main';
            },
            cacheGroups: {
                vendor: {
                    test: /[\\/]node_modules[\\/]/,
                    name: 'components/vendor',
                    chunks: 'initial'
                }
            }
        }
    }
};