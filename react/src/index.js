// react/src/index.js
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

// Wait for any existing app initialization if needed
const initReact = () => {
    const root = ReactDOM.createRoot(document.getElementById('root'));
    root.render(<App />);
};

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initReact);
} else {
    initReact();
}