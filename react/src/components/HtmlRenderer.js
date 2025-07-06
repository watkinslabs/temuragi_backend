import React, { useEffect, useRef } from 'react';

const HtmlRenderer = ({ html, config }) => {
    const container_ref = useRef(null);

    useEffect(() => {
        if (!html || !container_ref.current) return;

        // Inject the HTML
        container_ref.current.innerHTML = html;

        // If there are any scripts in the HTML, we need to recreate them
        const scripts = container_ref.current.querySelectorAll('script');
        scripts.forEach(old_script => {
            const new_script = document.createElement('script');
            
            // Copy attributes
            Array.from(old_script.attributes).forEach(attr => {
                new_script.setAttribute(attr.name, attr.value);
            });
            
            // Copy content
            new_script.textContent = old_script.textContent;
            
            // Replace old script with new one
            old_script.parentNode.replaceChild(new_script, old_script);
        });

        // Apply any config-based initialization
        if (config && window.initializePage) {
            window.initializePage(config);
        }
    }, [html, config]);

    return <div ref={container_ref} className="html-renderer" />;
};

export default HtmlRenderer;