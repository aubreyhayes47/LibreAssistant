// Markdown rendering utilities with XSS protection
// This module provides safe markdown rendering for chat messages

/**
 * Detects if content likely contains markdown formatting
 * @param {string} content - The text content to check
 * @returns {boolean} - True if content appears to contain markdown
 */
function hasMarkdownContent(content) {
    if (typeof content !== 'string' || !content.trim()) {
        return false;
    }
    
    // Common markdown patterns to detect
    const markdownPatterns = [
        /```[\s\S]*```/,          // Code blocks
        /`[^`]+`/,                // Inline code
        /^#{1,6}\s+/m,            // Headers
        /^\s*[-*+]\s+/m,          // Unordered lists
        /^\s*\d+\.\s+/m,          // Ordered lists
        /\*\*[^*]+\*\*/,          // Bold text
        /\*[^*]+\*/,              // Italic text
        /\[[^\]]+\]\([^)]+\)/,    // Links
        /^\s*>\s+/m,              // Blockquotes
        /\|[^|]+\|/,              // Tables
        /^---+$/m,                // Horizontal rules
    ];
    
    return markdownPatterns.some(pattern => pattern.test(content));
}

/**
 * Renders markdown content safely with XSS protection
 * @param {string} content - The markdown content to render
 * @returns {string} - Safe HTML string
 */
function renderMarkdown(content) {
    try {
        // Use marked to parse markdown if available
        if (typeof marked !== 'undefined') {
            // Configure marked for security and basic settings
            marked.setOptions({
                gfm: true,
                breaks: true,
                sanitize: false, // We'll use DOMPurify for sanitization
                smartypants: false,
                xhtml: false
            });
            
            // Parse markdown with default renderers
            let html = marked.parse(content);
            
            // Sanitize with DOMPurify if available
            if (typeof DOMPurify !== 'undefined') {
                html = DOMPurify.sanitize(html, {
                    ALLOWED_TAGS: [
                        'p', 'br', 'strong', 'em', 'code', 'pre', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                        'ul', 'ol', 'li', 'blockquote', 'a', 'img', 'table', 'thead', 'tbody', 'tr', 'td', 'th',
                        'hr', 'del', 'ins', 'sub', 'sup'
                    ],
                    ALLOWED_ATTR: ['href', 'title', 'alt', 'src', 'class', 'start'],
                    ALLOW_DATA_ATTR: false,
                    FORBID_TAGS: ['script', 'object', 'embed', 'style', 'link'],
                    FORBID_ATTR: ['onerror', 'onload', 'onclick', 'onmouseover', 'onfocus', 'onblur']
                });
            }
            
            return html;
        }
    } catch (error) {
        console.warn('Error rendering markdown:', error);
    }
    
    // Fallback: return escaped text if markdown parsing fails
    return escapeHtml(content);
}

/**
 * Escapes HTML characters for safe display
 * @param {string} text - The text to escape
 * @returns {string} - Escaped HTML
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Renders content as either markdown or plain text based on detection
 * @param {string} content - The content to render
 * @returns {string} - Safe HTML string
 */
function renderChatContent(content) {
    if (!content || typeof content !== 'string') {
        return '';
    }
    
    // Auto-detect and render markdown, or fall back to plain text
    if (hasMarkdownContent(content)) {
        return renderMarkdown(content);
    } else {
        return escapeHtml(content);
    }
}

// Export functions for use in different contexts
if (typeof module !== 'undefined' && module.exports) {
    // Node.js environment
    module.exports = {
        hasMarkdownContent,
        renderMarkdown,
        renderChatContent,
        escapeHtml
    };
} else {
    // Browser environment - attach to window
    window.MarkdownUtils = {
        hasMarkdownContent,
        renderMarkdown,
        renderChatContent,
        escapeHtml
    };
}