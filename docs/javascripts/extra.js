/* Extra JavaScript for Blender Remote documentation */

document.addEventListener('DOMContentLoaded', function() {
    // Add copy button to code blocks
    addCopyButtonsToCodeBlocks();
    
    // Add interactive examples
    addInteractiveExamples();
    
    // Add API method anchors
    addApiMethodAnchors();
    
    // Add search functionality enhancements
    enhanceSearch();
});

/**
 * Add copy buttons to code blocks
 */
function addCopyButtonsToCodeBlocks() {
    const codeBlocks = document.querySelectorAll('pre code');
    
    codeBlocks.forEach(function(codeBlock) {
        const pre = codeBlock.parentElement;
        
        // Skip if already has copy button
        if (pre.querySelector('.copy-button')) return;
        
        // Create copy button
        const copyButton = document.createElement('button');
        copyButton.className = 'copy-button';
        copyButton.textContent = 'Copy';
        copyButton.setAttribute('title', 'Copy to clipboard');
        
        // Add click handler
        copyButton.addEventListener('click', function() {
            navigator.clipboard.writeText(codeBlock.textContent).then(function() {
                copyButton.textContent = 'Copied!';
                copyButton.classList.add('copied');
                
                setTimeout(function() {
                    copyButton.textContent = 'Copy';
                    copyButton.classList.remove('copied');
                }, 2000);
            }).catch(function(err) {
                console.error('Failed to copy text: ', err);
                copyButton.textContent = 'Failed';
                setTimeout(function() {
                    copyButton.textContent = 'Copy';
                }, 2000);
            });
        });
        
        // Position button
        pre.style.position = 'relative';
        copyButton.style.position = 'absolute';
        copyButton.style.top = '8px';
        copyButton.style.right = '8px';
        copyButton.style.padding = '4px 8px';
        copyButton.style.fontSize = '12px';
        copyButton.style.border = '1px solid #ccc';
        copyButton.style.borderRadius = '4px';
        copyButton.style.backgroundColor = '#f8f9fa';
        copyButton.style.cursor = 'pointer';
        copyButton.style.zIndex = '1';
        
        pre.appendChild(copyButton);
    });
}

/**
 * Add interactive examples for API calls
 */
function addInteractiveExamples() {
    const apiExamples = document.querySelectorAll('.api-example');
    
    apiExamples.forEach(function(example) {
        const tryButton = document.createElement('button');
        tryButton.textContent = 'Try in Console';
        tryButton.className = 'try-button';
        
        tryButton.addEventListener('click', function() {
            const code = example.querySelector('code').textContent;
            console.log('Example code:', code);
            
            // Show in a modal or expand section
            showCodeInConsole(code);
        });
        
        example.appendChild(tryButton);
    });
}

/**
 * Show code in an interactive console
 */
function showCodeInConsole(code) {
    // Create modal overlay
    const overlay = document.createElement('div');
    overlay.className = 'console-overlay';
    overlay.style.position = 'fixed';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.width = '100%';
    overlay.style.height = '100%';
    overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
    overlay.style.zIndex = '9999';
    overlay.style.display = 'flex';
    overlay.style.alignItems = 'center';
    overlay.style.justifyContent = 'center';
    
    // Create console window
    const consoleWindow = document.createElement('div');
    consoleWindow.style.backgroundColor = '#1e1e1e';
    consoleWindow.style.color = '#d4d4d4';
    consoleWindow.style.padding = '20px';
    consoleWindow.style.borderRadius = '8px';
    consoleWindow.style.width = '80%';
    consoleWindow.style.maxWidth = '800px';
    consoleWindow.style.maxHeight = '80%';
    consoleWindow.style.overflow = 'auto';
    consoleWindow.style.fontFamily = 'Monaco, Consolas, monospace';
    
    // Add close button
    const closeButton = document.createElement('button');
    closeButton.textContent = '×';
    closeButton.style.position = 'absolute';
    closeButton.style.top = '10px';
    closeButton.style.right = '15px';
    closeButton.style.background = 'none';
    closeButton.style.border = 'none';
    closeButton.style.color = '#d4d4d4';
    closeButton.style.fontSize = '24px';
    closeButton.style.cursor = 'pointer';
    
    closeButton.addEventListener('click', function() {
        document.body.removeChild(overlay);
    });
    
    // Add code
    const codeElement = document.createElement('pre');
    codeElement.textContent = code;
    codeElement.style.margin = '0';
    codeElement.style.whiteSpace = 'pre-wrap';
    
    consoleWindow.style.position = 'relative';
    consoleWindow.appendChild(closeButton);
    consoleWindow.appendChild(codeElement);
    overlay.appendChild(consoleWindow);
    
    // Close on background click
    overlay.addEventListener('click', function(e) {
        if (e.target === overlay) {
            document.body.removeChild(overlay);
        }
    });
    
    document.body.appendChild(overlay);
}

/**
 * Add anchor links to API methods
 */
function addApiMethodAnchors() {
    const apiMethods = document.querySelectorAll('.api-method h5');
    
    apiMethods.forEach(function(method) {
        const anchor = document.createElement('a');
        anchor.href = '#' + method.textContent.toLowerCase().replace(/[^\w]/g, '-');
        anchor.className = 'api-anchor';
        anchor.textContent = '#';
        anchor.style.marginLeft = '8px';
        anchor.style.color = '#666';
        anchor.style.textDecoration = 'none';
        anchor.style.fontSize = '14px';
        
        anchor.addEventListener('mouseover', function() {
            anchor.style.color = '#007acc';
        });
        
        anchor.addEventListener('mouseout', function() {
            anchor.style.color = '#666';
        });
        
        method.appendChild(anchor);
    });
}

/**
 * Enhance search functionality
 */
function enhanceSearch() {
    // Add search suggestions for API methods
    const searchInput = document.querySelector('[data-md-component="search-query"]');
    
    if (searchInput) {
        const apiMethods = [
            'connect', 'disconnect', 'create_primitive', 'render',
            'set_camera_location', 'create_light', 'save_file'
        ];
        
        searchInput.addEventListener('input', function() {
            const value = this.value.toLowerCase();
            
            if (value.length > 2) {
                const suggestions = apiMethods.filter(method => 
                    method.includes(value)
                );
                
                // You could display suggestions here
                console.log('Search suggestions:', suggestions);
            }
        });
    }
}

/**
 * Add keyboard shortcuts
 */
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K to focus search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('[data-md-component="search-query"]');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // Escape to close modals
    if (e.key === 'Escape') {
        const overlay = document.querySelector('.console-overlay');
        if (overlay) {
            document.body.removeChild(overlay);
        }
    }
});

/**
 * Add smooth scrolling for anchor links
 */
document.addEventListener('click', function(e) {
    if (e.target.matches('a[href^="#"]')) {
        e.preventDefault();
        const targetId = e.target.getAttribute('href').substring(1);
        const targetElement = document.getElementById(targetId);
        
        if (targetElement) {
            targetElement.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    }
});

/**
 * Add version compatibility warnings
 */
function addVersionWarnings() {
    const versionElements = document.querySelectorAll('.version-added, .version-changed');
    
    versionElements.forEach(function(element) {
        element.style.fontSize = '12px';
        element.style.padding = '2px 6px';
        element.style.borderRadius = '3px';
        element.style.backgroundColor = '#e3f2fd';
        element.style.color = '#1976d2';
        element.style.border = '1px solid #bbdefb';
    });
}

// Initialize additional features
document.addEventListener('DOMContentLoaded', function() {
    addVersionWarnings();
});

// Add CSS for copy buttons
const style = document.createElement('style');
style.textContent = `
    .copy-button {
        opacity: 0;
        transition: opacity 0.2s;
    }
    
    pre:hover .copy-button {
        opacity: 1;
    }
    
    .copy-button.copied {
        background-color: #28a745 !important;
        color: white !important;
        border-color: #28a745 !important;
    }
    
    .try-button {
        margin-top: 8px;
        padding: 6px 12px;
        background-color: #007acc;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 12px;
    }
    
    .try-button:hover {
        background-color: #005a9e;
    }
`;
document.head.appendChild(style);