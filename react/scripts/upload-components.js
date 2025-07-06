#!/usr/bin/env node
require('dotenv').config();

const fs = require('fs');
const path = require('path');
const glob = require('glob');

function parse_routes_from_source(source_code, component_name) {
    const routes = [];
    
    // Method 1: Check for @routes in JSDoc comments
    const jsdoc_pattern = /@routes\s*\[(.*?)\]/;
    const jsdoc_match = source_code.match(jsdoc_pattern);
    if (jsdoc_match) {
        const routes_string = jsdoc_match[1];
        const route_matches = routes_string.match(/["'`]([^"'`]+)["'`]/g);
        if (route_matches) {
            return route_matches.map(r => r.replace(/["'`]/g, ''));
        }
    }
    
    // Method 2: Check for ROUTES: comment
    const comment_pattern = /\/\/\s*ROUTES?:\s*(.+)/i;
    const comment_match = source_code.match(comment_pattern);
    if (comment_match) {
        return comment_match[1].split(',').map(r => r.trim());
    }
    
    // Method 3: Check for static routes property
    const static_pattern = new RegExp(`${component_name}\\.routes\\s*=\\s*\\[(.*?)\\]`, 's');
    const static_match = source_code.match(static_pattern);
    if (static_match) {
        const routes_string = static_match[1];
        const route_matches = routes_string.match(/["'`]([^"'`]+)["'`]/g);
        if (route_matches) {
            return route_matches.map(r => r.replace(/["'`]/g, ''));
        }
    }
    
    // Method 4: Generate default route from component name
    // HomePage -> /home-page, UserDashboard -> /user-dashboard
    const default_route = '/' + component_name
        .replace(/([A-Z])/g, '-$1')
        .toLowerCase()
        .replace(/^-/, '');
    
    console.log(`  No explicit routes found, using default: ${default_route}`);
    return [default_route];
}

async function uploadComponents() {
    const API_BASE = process.env.API_BASE || 'http://localhost:5000';
    const API_TOKEN = process.env.API_TOKEN;

    if (!API_TOKEN) {
        console.error('ERROR: API_TOKEN environment variable is required');
        console.error('Usage: API_TOKEN="your-token" npm run build:components');
        process.exit(1);
    }

    console.log(`Using API base: ${API_BASE}`);

    // Find built component files in both components and user_components directories
    const component_search_path = path.join(__dirname, '../../app/static/js/components/*.bundle.js');
    const user_component_search_path = path.join(__dirname, '../../app/static/js/user_components/*.bundle.js');
    
    console.log(`Searching for bundles in:`);
    console.log(`  - ${component_search_path}`);
    console.log(`  - ${user_component_search_path}`);
    
    // Get files from both directories
    const component_files = glob.sync(component_search_path).filter(file => !file.includes('vendor.bundle.js'));
    const user_component_files = glob.sync(user_component_search_path);
    
    // Combine all files with their source directory info
    const all_component_files = [
        ...component_files.map(file => ({ file, source_dir: 'components' })),
        ...user_component_files.map(file => ({ file, source_dir: 'user_components' }))
    ];

    console.log(`Found ${component_files.length} component bundles`);
    console.log(`Found ${user_component_files.length} user component bundles`);
    console.log(`Total: ${all_component_files.length} bundles to upload`);

    for (const { file, source_dir } of all_component_files) {
        const component_name = path.basename(file, '.bundle.js');
        const compiled_code = fs.readFileSync(file, 'utf8');

        // Look for source file in the appropriate directory
        let source_code = '';
        let source_found = false;

        // Try to find source file in the corresponding source directory
        const source_path = path.join(__dirname, `../src/${source_dir}/${component_name}.js`);
        
        if (fs.existsSync(source_path)) {
            source_code = fs.readFileSync(source_path, 'utf8');
            source_found = true;
            console.log(`Found source for ${component_name} at ${source_path}`);
        } else {
            // If not found in expected location, try the other directory
            const alt_source_dir = source_dir === 'components' ? 'user_components' : 'components';
            const alt_source_path = path.join(__dirname, `../src/${alt_source_dir}/${component_name}.js`);
            
            if (fs.existsSync(alt_source_path)) {
                source_code = fs.readFileSync(alt_source_path, 'utf8');
                source_found = true;
                console.log(`Found source for ${component_name} at ${alt_source_path} (alternate location)`);
            }
        }

        if (!source_found) {
            console.warn(`⚠ Source file not found for ${component_name}, skipping...`);
            continue;
        }

        console.log(`Uploading ${component_name} (from ${source_dir})...`);

        // Parse routes from source code
        const routes = parse_routes_from_source(source_code, component_name);
        console.log(`  Routes: ${routes.join(', ') || 'none'}`);

        try {
            const response = await fetch(`${API_BASE}/v2/api/components/sync`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${API_TOKEN}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: component_name,
                    source_code: source_code,
                    compiled_code: compiled_code,
                    version: '1.0.0',
                    description: `Component ${component_name}`,
                    routes: routes
                })
            });

            const result = await response.json();

            if (response.ok) {
                console.log(`✓ ${component_name} ${result.status} (build #${result.build_number})`);
            } else {
                console.error(`✗ ${component_name} failed:`, result.error || 'Unknown error');
                console.error(`  Status: ${response.status} ${response.statusText}`);
            }
        } catch (error) {
            console.error(`✗ ${component_name} failed:`, error.message);
        }
    }

    console.log('\nUpload complete!');
}

// Run if called directly
if (require.main === module) {
    uploadComponents().catch(console.error);
}

module.exports = { uploadComponents };