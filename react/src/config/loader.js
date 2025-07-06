// react/src/config/loader.js
export const loadConfig = async () => {
    try {
        const response = await fetch('/api/config');
        const serverConfig = await response.json();
        
        // Merge with default config
        return { ...config, ...serverConfig };
    } catch (error) {
        console.warn('Failed to load server config, using defaults');
        return config;
    }
};