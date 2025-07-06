import React, { useState, useRef } from 'react';
import config from '../config';

const ComponentBuilder = () => {
    const [component_name, setComponentName] = useState('');
    const [component_code, setComponentCode] = useState('');
    const [style_code, setStyleCode] = useState('');
    const [description, setDescription] = useState('');
    const [preview_mode, setPreviewMode] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
    const preview_ref = useRef(null);

    const default_template = `// Define your component
const Component = () => {
    const [count, setCount] = useState(0);

    return (
        <div className="custom-component">
            <h2>My Custom Component</h2>
            <p>Count: {count}</p>
            <button
                onClick={() => setCount(count + 1)}
                className="btn btn-primary"
            >
                Increment
            </button>
        </div>
    );
};

// Component must be the last expression`;

    const handlePreview = () => {
        setError(null);
        try {
            // Create sandbox globals
            const sandbox_globals = {
                React,
                useState: React.useState,
                useEffect: React.useEffect,
                useCallback: React.useCallback,
                useMemo: React.useMemo,
                useRef: React.useRef,
            };

            // Test compile the component
            const component_function = new Function(
                ...Object.keys(sandbox_globals),
                `
                ${component_code || default_template}
                return Component;
                `
            );

            const TestComponent = component_function(...Object.values(sandbox_globals));

            // Render preview
            setPreviewMode(true);

            // Clear previous preview
            if (preview_ref.current) {
                const root = ReactDOM.createRoot(preview_ref.current);
                root.render(<TestComponent />);
            }
        } catch (err) {
            setError(`Preview error: ${err.message}`);
            setPreviewMode(false);
        }
    };

    const handleSave = async () => {
        setError(null);
        setSuccess(null);

        if (!component_name || !component_code) {
            setError('Component name and code are required');
            return;
        }

        try {
            const response = await config.apiCall(config.getUrl('/components'), {
                method: 'POST',
                headers: config.getAuthHeaders(),
                body: JSON.stringify({
                    name: component_name,
                    component_code: component_code,
                    style_code: style_code,
                    description: description,
                    default_props: {}
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to save component');
            }

            setSuccess(`Component "${data.name}" created successfully!`);

            // Reset form
            setComponentName('');
            setComponentCode('');
            setStyleCode('');
            setDescription('');
            setPreviewMode(false);
        } catch (err) {
            setError(err.message);
        }
    };

    return (
        <div className="container-fluid mt-4">
            <div className="row">
                <div className="col-lg-6">
                    <div className="card">
                        <div className="card-header">
                            <h4>Component Builder</h4>
                        </div>
                        <div className="card-body">
                            {error && (
                                <div className="alert alert-danger">{error}</div>
                            )}
                            {success && (
                                <div className="alert alert-success">{success}</div>
                            )}

                            <div className="mb-3">
                                <label className="form-label">Component Name (PascalCase)</label>
                                <input
                                    type="text"
                                    className="form-control"
                                    value={component_name}
                                    onChange={(e) => setComponentName(e.target.value)}
                                    placeholder="MyCustomComponent"
                                />
                            </div>

                            <div className="mb-3">
                                <label className="form-label">Description</label>
                                <textarea
                                    className="form-control"
                                    rows="2"
                                    value={description}
                                    onChange={(e) => setDescription(e.target.value)}
                                    placeholder="Describe what this component does..."
                                />
                            </div>

                            <div className="mb-3">
                                <label className="form-label">Component Code (React/JSX)</label>
                                <textarea
                                    className="form-control font-monospace"
                                    rows="15"
                                    value={component_code}
                                    onChange={(e) => setComponentCode(e.target.value)}
                                    placeholder={default_template}
                                />
                            </div>

                            <div className="mb-3">
                                <label className="form-label">CSS Styles (Optional)</label>
                                <textarea
                                    className="form-control font-monospace"
                                    rows="5"
                                    value={style_code}
                                    onChange={(e) => setStyleCode(e.target.value)}
                                    placeholder=".custom-component { padding: 20px; }"
                                />
                            </div>

                            <div className="d-flex gap-2">
                                <button
                                    className="btn btn-secondary"
                                    onClick={handlePreview}
                                >
                                    Preview
                                </button>
                                <button
                                    className="btn btn-primary"
                                    onClick={handleSave}
                                    disabled={!component_name || !component_code}
                                >
                                    Save Component
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="col-lg-6">
                    <div className="card">
                        <div className="card-header">
                            <h4>Preview</h4>
                        </div>
                        <div className="card-body">
                            {preview_mode ? (
                                <>
                                    {style_code && (
                                        <style dangerouslySetInnerHTML={{ __html: style_code }} />
                                    )}
                                    <div ref={preview_ref} />
                                </>
                            ) : (
                                <div className="text-muted text-center p-5">
                                    Click "Preview" to see your component
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="card mt-3">
                        <div className="card-header">
                            <h5>Available APIs</h5>
                        </div>
                        <div className="card-body">
                            <pre className="bg-light p-3 rounded">{`// React Hooks
const [state, setState] = useState(initialValue);
useEffect(() => { ... }, [dependencies]);
const memoized = useMemo(() => computeValue, [deps]);
const callback = useCallback(() => { ... }, [deps]);
const ref = useRef(initialValue);

// API Calls
api.get('/endpoint') // GET request
api.post('/endpoint', { data }) // POST request

// Component must return JSX
return <div>Your content</div>;

// Access component props
const Component = ({ config }) => {
    // Use config passed from route
};`}</pre>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ComponentBuilder;