<!-- Copyright (c) 2024 LibreAssistant contributors. Licensed under the MIT License. -->

# UI Package

This directory contains standalone web components and the assets needed to style them.

```text
ui/
  components/          # individual custom element modules
  tokens.css           # shared design tokens and built-in theme variables
  theme-catalog.json   # metadata for built-in and community themes
  themes/              # sanitized CSS for each theme listed in the catalog
```

## Quick Start for Developers

To get started with UI development:

1. **Install Dependencies**:
   ```bash
   npm install
   ```

2. **Run Tests**:
   ```bash
   npm run test:ui
   npm run test:accessibility
   ```

3. **Development Workflow**:
   ```bash
   # Start the main application
   docker compose up --build
   
   # In another terminal, work on components
   cd ui/components
   # Edit your components and test in browser at localhost:8000
   ```

4. **Theme Development**:
   ```bash
   # Create a new theme
   mkdir community-themes/my-theme
   # Edit theme files, then build
   python scripts/build_theme_catalog.py
   ```

## Core Development Workflows

### 1. Component Development

Each component is a self-contained web component:

```js
// Example: creating a new component
class MyComponent extends HTMLElement {
  connectedCallback() {
    this.innerHTML = `
      <style>
        :host {
          display: block;
          color: var(--color-primary);
        }
      </style>
      <div>My Custom Component</div>
    `;
  }
}

customElements.define('my-component', MyComponent);
```

**Testing Components**:
```bash
# Run component tests
npm run test:ui

# Test accessibility
npm run test:accessibility
npm run audit:contrast
```

### 2. Theme Development Workflow

1. **Create Theme Structure**:
   ```bash
   mkdir community-themes/my-awesome-theme
   cd community-themes/my-awesome-theme
   ```

2. **Define Theme Metadata** (`metadata.json`):
   ```json
   {
     "name": "My Awesome Theme",
     "author": "Your Name",
     "description": "A beautiful theme for LibreAssistant",
     "preview": "#4a90e2",
     "version": "1.0.0"
   }
   ```

3. **Create Theme Styles** (`theme.css`):
   ```css
   :root {
     /* Primary colors */
     --color-primary: #4a90e2;
     --color-primary-hover: #357abd;
     
     /* Background colors */
     --color-background: #ffffff;
     --color-surface: #f8f9fa;
     
     /* Text colors */
     --color-text: #333333;
     --color-text-muted: #666666;
     
     /* Component specific */
     --button-radius: 8px;
     --input-border: 1px solid #e1e5e9;
   }
   ```

4. **Build and Test**:
   ```bash
   python scripts/build_theme_catalog.py
   # Test your theme at localhost:8000
   ```

### 3. Component Integration

Adding new components to the application:

1. **Create Component File**: `ui/components/my-component.js`
2. **Import in Application**: Add to main component loader
3. **Use in Templates**: `<my-component></my-component>`

### 4. Design Token Management

The design system uses CSS custom properties for consistency:

```css
/* tokens.css structure */
:root {
  /* Spacing scale */
  --space-xs: 0.25rem;
  --space-sm: 0.5rem;
  --space-md: 1rem;
  --space-lg: 1.5rem;
  --space-xl: 2rem;
  
  /* Typography scale */
  --font-size-sm: 0.875rem;
  --font-size-base: 1rem;
  --font-size-lg: 1.125rem;
  --font-size-xl: 1.25rem;
  
  /* Color system */
  --color-primary: #007bff;
  --color-success: #28a745;
  --color-warning: #ffc107;
  --color-danger: #dc3545;
}
```

## Components

Each file in `components/` defines a web component and registers it with
`customElements.define()`. Components can be loaded on demand by importing their
module:

```js
import './components/primary-button.js';
```

After the import, the `<primary-button>` tag becomes available to the page. This
pattern keeps bundles small and allows the runtime to lazy‑load components when
needed.

### Component Lifecycle

Components follow the standard Web Component lifecycle:

```js
class MyComponent extends HTMLElement {
  constructor() {
    super();
    // Initialize component state
  }
  
  connectedCallback() {
    // Component added to DOM
    this.render();
    this.attachEventListeners();
  }
  
  disconnectedCallback() {
    // Component removed from DOM
    this.cleanup();
  }
  
  attributeChangedCallback(name, oldValue, newValue) {
    // Attribute changed
    this.handleAttributeChange(name, oldValue, newValue);
  }
  
  static get observedAttributes() {
    return ['data-theme', 'disabled'];
  }
}
```

### Component Communication

Components communicate through events and shared state:

```js
// Dispatch custom events
this.dispatchEvent(new CustomEvent('component-action', {
  detail: { action: 'save', data: formData },
  bubbles: true
}));

// Listen for events
document.addEventListener('component-action', (event) => {
  console.log('Action:', event.detail.action);
});

// Use shared state for global data
import { sharedState } from './shared-state.js';
sharedState.subscribe('theme', (newTheme) => {
  this.updateTheme(newTheme);
});
```

## Design tokens

`tokens.css` exposes the shared design tokens used across all components. It
contains typography, spacing and radius scales as well as color variables for
the built‑in light, dark and high‑contrast themes. The stylesheet should be
loaded once at application start so every component can reference the tokens.

## Themes

LibreAssistant uses a comprehensive theming system that allows for easy customization of the entire interface.

### Theme Structure

`theme-catalog.json` enumerates all available themes:

```json
{
  "themes": [
    {
      "id": "my-theme",
      "name": "My Custom Theme",
      "author": "Your Name",
      "description": "A beautiful custom theme",
      "preview": "#4a90e2",
      "version": "1.0.0",
      "rating": 5
    }
  ]
}
```

### Built-in Themes

LibreAssistant comes with several built-in themes:

- **Light**: Clean, minimal light theme with high readability
- **Dark**: Modern dark theme easy on the eyes
- **High Contrast**: Accessibility-focused theme with maximum contrast

### Custom Theme Development

1. **Create Theme Directory**:
   ```bash
   mkdir community-themes/my-theme
   cd community-themes/my-theme
   ```

2. **Theme Metadata** (`metadata.json`):
   ```json
   {
     "name": "My Amazing Theme",
     "author": "Your Name",
     "description": "A description of your theme",
     "preview": "#your-primary-color",
     "version": "1.0.0"
   }
   ```

3. **Theme Styles** (`theme.css`):
   ```css
   :root {
     /* Core color palette */
     --color-primary: #4a90e2;
     --color-primary-hover: #357abd;
     --color-background: #ffffff;
     --color-surface: #f8f9fa;
     --color-text: #333333;
     
     /* Component-specific variables */
     --button-background: var(--color-primary);
     --button-text: #ffffff;
     --input-background: var(--color-surface);
     --input-border: #e1e5e9;
     
     /* Spacing and typography */
     --border-radius: 6px;
     --shadow: 0 2px 4px rgba(0,0,0,0.1);
   }
   ```

4. **Build and Deploy**:
   ```bash
   # From project root
   python scripts/build_theme_catalog.py
   # Your theme is now available in the UI
   ```

### Theme Testing

Test your theme across all components:

```bash
# Validate accessibility
npm run audit:contrast

# Test theme marketplace integration
python scripts/test_theme_marketplace.py

# Validate all themes
python scripts/validate_themes.py
```

## Advanced Customization

### Creating Interactive Components

Build components that integrate with the LibreAssistant API:

```js
class ApiIntegratedComponent extends HTMLElement {
  async connectedCallback() {
    this.innerHTML = `
      <style>
        :host {
          display: block;
          padding: var(--space-md);
          border: var(--input-border);
          border-radius: var(--border-radius);
        }
        .loading { opacity: 0.6; }
      </style>
      <div id="content">Loading...</div>
    `;
    
    await this.loadData();
  }
  
  async loadData() {
    try {
      const response = await fetch('/api/v1/health');
      const data = await response.json();
      this.querySelector('#content').textContent = 
        `System Status: ${data.status}`;
    } catch (error) {
      this.querySelector('#content').textContent = 'Error loading data';
    }
  }
}

customElements.define('api-integrated-component', ApiIntegratedComponent);
```

### Theme Validation and Testing

Ensure your themes meet accessibility standards:

```bash
# Validate theme accessibility
npm run audit:contrast

# Fix contrast issues automatically
npm run fix:contrast

# Test themes across components
python scripts/validate_themes.py
```

### Component State Management

For complex components, use a simple state pattern:

```js
class StatefulComponent extends HTMLElement {
  constructor() {
    super();
    this.state = {
      count: 0,
      loading: false
    };
  }
  
  setState(newState) {
    this.state = { ...this.state, ...newState };
    this.render();
  }
  
  render() {
    this.innerHTML = `
      <div>Count: ${this.state.count}</div>
      <button onclick="this.increment()">
        ${this.state.loading ? 'Loading...' : 'Increment'}
      </button>
    `;
  }
  
  increment() {
    this.setState({ count: this.state.count + 1 });
  }
}
```

### Responsive Design Patterns

Use CSS Grid and Flexbox with design tokens:

```css
.responsive-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--space-md);
  padding: var(--space-lg);
}

@media (max-width: 768px) {
  .responsive-grid {
    grid-template-columns: 1fr;
    gap: var(--space-sm);
    padding: var(--space-md);
  }
}
```

### Performance Optimization

Optimize component loading and rendering:

```js
// Lazy load components
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      import('./components/heavy-component.js');
      observer.unobserve(entry.target);
    }
  });
});

// Use requestAnimationFrame for smooth animations
class AnimatedComponent extends HTMLElement {
  animate() {
    const step = (timestamp) => {
      // Animation logic here
      if (this.shouldContinue) {
        requestAnimationFrame(step);
      }
    };
    requestAnimationFrame(step);
  }
}
```

## Web Component Loading

The application uses a smart loading system that dynamically imports components as needed:

```js
// Component loader pattern
class ComponentLoader {
  static async loadComponent(tagName) {
    const componentMap = {
      'primary-button': () => import('./components/primary-button.js'),
      'theme-selector': () => import('./components/theme-selector.js'),
      'plugin-catalogue': () => import('./components/plugin-catalogue.js')
    };
    
    if (componentMap[tagName]) {
      await componentMap[tagName]();
    }
  }
  
  static observeDOM() {
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === Node.ELEMENT_NODE) {
            this.loadComponentsInElement(node);
          }
        });
      });
    });
    
    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }
}
```

This approach ensures:
- **Faster initial load**: Only essential components are loaded upfront
- **Lazy loading**: Components load when actually needed
- **Better performance**: Reduced bundle size and memory usage
- **Modularity**: Each component is independently loadable

### Best Practices

1. **Keep components focused**: Each component should have a single responsibility
2. **Use design tokens**: Leverage CSS custom properties for consistent styling
3. **Handle loading states**: Show appropriate feedback while components load
4. **Test accessibility**: Ensure components work with screen readers and keyboard navigation
5. **Performance**: Use `requestAnimationFrame` for smooth animations and heavy computations
