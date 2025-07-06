#!/usr/bin/env node

require('dotenv').config();

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const glob = require('glob');

async function fetchComponents() {
    const API_BASE = process.env.API_BASE || 'http://localhost:5000';
    const API_TOKEN = process.env.API_TOKEN;

    if (!API_TOKEN) {
        console.error('ERROR: API_TOKEN environment variable is required');
        process.exit(1);
    }

    const response = await fetch(`${API_BASE}/v2/api/components/export`, {
        headers: {
            'Authorization': `Bearer ${API_TOKEN}`
        }
    });

    if (!response.ok) {
        throw new Error('Failed to fetch components');
    }

    return await response.json();
}

async function buildComponents() {
    console.log('Building components from local files and database...');

    try {
        // First, fetch and build database components
        console.log('\n1. Fetching components from database...');
        const db_components = await fetchComponents();

        // Create dynamic components directory
        const dynamic_dir = path.join(__dirname, '../src/components/dynamic');
        if (!fs.existsSync(dynamic_dir)) {
            fs.mkdirSync(dynamic_dir, { recursive: true });
        }

        // Clean old dynamic components
        const existing_files = fs.readdirSync(dynamic_dir);
        existing_files.forEach(file => {
            fs.unlinkSync(path.join(dynamic_dir, file));
        });

        // Create component files from database
        db_components.forEach(component => {
            const file_content = `
// Auto-generated component: ${component.name}
// Version: ${component.version}
// Generated: ${new Date().toISOString()}

import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';

${component.component_code}

// Make sure Component is defined for the wrapper
const Component = ${component.name};
export default Component;
`;

            const file_path = path.join(dynamic_dir, `${component.name}.js`);
            fs.writeFileSync(file_path, file_content);
            console.log(`Created dynamic component: ${component.name}`);
        });

        console.log(`Created ${db_components.length} dynamic component files`);

        // Now find all components to build (local + user + dynamic)
        console.log('\n2. Finding all components to build...');
        
        // System components that should be excluded from build
        const system_components = [
            'DynamicPage',
            'LoadingScreen', 
            'Login',
            'HtmlRenderer',
            'ComponentBuilder',
            'AuthContext'
        ];

        // Find components in main components directory
        const main_components = glob.sync('./src/components/*.js')
            .map(file => ({
                path: file,
                name: path.basename(file, '.js'),
                type: 'main'
            }))
            .filter(comp => !system_components.includes(comp.name));

        // Find components in user_components directory
        const user_components = glob.sync('./src/components/user_components/*.js')
            .map(file => ({
                path: file,
                name: path.basename(file, '.js'),
                type: 'user'
            }));

        // Find dynamic components (from database)
        const dynamic_components = glob.sync('./src/components/dynamic/*.js')
            .map(file => ({
                path: file,
                name: path.basename(file, '.js'),
                type: 'dynamic'
            }));

        // Combine all components
        const all_components = [...main_components, ...user_components, ...dynamic_components];

        console.log(`\nFound components to build:`);
        console.log(`- Main components: ${main_components.length}`);
        console.log(`- User components: ${user_components.length}`);
        console.log(`- Dynamic components: ${dynamic_components.length}`);
        console.log(`- Total: ${all_components.length}`);

        if (all_components.length === 0) {
            console.log('\nNo components to build!');
            return;
        }

        // Create webpack entries for all components
        const entries = {};
        all_components.forEach(comp => {
            entries[comp.name] = path.resolve(comp.path);
        });

        // Create webpack config
        const webpack_config = {
            mode: 'production',
            entry: entries,
            output: {
                path: path.resolve(__dirname, '../../app/static/js/components'),
                filename: '[name].bundle.js',
                library: ['Components', '[name]'],
                libraryTarget: 'window'
            },
            module: {
                rules: [
                    {
                        test: /\.js$/,
                        exclude: /node_modules/,
                        use: {
                            loader: 'babel-loader',
                            options: {
                                presets: ['@babel/preset-react']
                            }
                        }
                    }
                ]
            },
            externals: {
                'react': 'React',
                'react-dom': 'ReactDOM',
                'react-router-dom': 'ReactRouterDOM'
            }
        };

        // Write webpack config
        const webpack_config_path = path.join(__dirname, '../webpack.components.config.js');
        fs.writeFileSync(
            webpack_config_path,
            `module.exports = ${JSON.stringify(webpack_config, null, 2)};`
        );

        // Run webpack build
        console.log('\n3. Building components with webpack...');
        execSync(`npx webpack --config ${webpack_config_path}`, { stdio: 'inherit' });

        // Clean up webpack config
        fs.unlinkSync(webpack_config_path);

        console.log('\n✓ Build complete!');
        console.log(`Built ${all_components.length} components:`);
        all_components.forEach(comp => {
            console.log(`  - ${comp.name} (${comp.type})`);
        });

    } catch (error) {
        console.error('Build failed:', error);
        process.exit(1);
    }
}

if (require.main === module) {
    buildComponents();
}

module.exports = { buildComponents };