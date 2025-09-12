# 🎨 Changing Themes

LibreAssistant offers a comprehensive theming system that allows you to customize the appearance of your interface. Choose from built-in themes or install community-created themes to match your preferences.

## Overview

LibreAssistant's theming system supports:
- **Built-in Themes**: Light, Dark, and High Contrast themes
- **Community Themes**: User-contributed themes like Solarized
- **Custom Themes**: Create your own themes with CSS
- **Real-time Switching**: Change themes instantly without reloading

## Available Themes

### Built-in Themes

- **Light Theme**: Clean, bright interface ideal for daytime use
- **Dark Theme**: Easy on the eyes for low-light environments  
- **High Contrast**: Enhanced accessibility with high contrast colors

### Community Themes

- **Solarized**: Popular developer-friendly color scheme
- **Additional themes**: Check the Theme Marketplace for more options

## Step-by-Step Guide

### 1. Quick Theme Switching

The fastest way to change themes is through the theme selector:

1. **Locate Theme Selector**
   - Look for "Theme:" dropdown in the interface
   - It appears in multiple locations (settings, forms, etc.)

2. **Select New Theme**
   - Click the theme dropdown menu
   - Choose from available themes
   - The change applies immediately

![Theme switching interface](https://github.com/user-attachments/assets/5dd3d995-ed12-4cb1-8749-b2fc71dd214c)

### 2. Using the Theme Marketplace

For more theme options and installation features:

1. **Access Theme Marketplace**
   - Click on **Theme Marketplace** tab in the main navigation
   - Browse available themes with previews

2. **Preview Themes**
   - Each theme shows a preview with sample colors
   - View author information and descriptions

3. **Install New Themes**
   - Click "Install" button next to desired theme
   - Monitor the installation progress
   - Theme becomes available immediately after installation

### 3. Detailed Theme Installation Process

When installing a theme from the marketplace:

1. **Select Theme to Install**
   - Browse the marketplace for available themes
   - Read theme descriptions and author information
   - Check theme compatibility

2. **Begin Installation**
   - Click the "Install Theme" button
   - You'll see "Installing theme [Theme Name]..." message
   - Installation button shows loading spinner

3. **Monitor Progress**
   - Progress indicators show installation status
   - Real-time updates keep you informed
   - Button shows "Installing..." with visual feedback

4. **Installation Complete**
   - Success message: "Theme [Theme Name] installed successfully"
   - Theme is immediately applied to the interface
   - Install button returns to normal state

![Theme installation feedback](https://github.com/user-attachments/assets/4280a33c-9e83-4858-b06b-438a12c24af7)

### 4. Handling Installation Errors

If theme installation fails:

1. **Error Notification**
   - Clear error message appears
   - Install button returns to normal state
   - Page theme remains unchanged

2. **Common Solutions**
   - Check internet connection
   - Verify theme compatibility
   - Try installing again later
   - Contact theme author if persistent issues

## Understanding Theme Components

### Color Schemes

LibreAssistant themes control:
- **Background colors**: Main interface backgrounds
- **Text colors**: Primary and secondary text
- **Accent colors**: Buttons, links, and highlights
- **Border colors**: Component boundaries and dividers
- **Status colors**: Success, error, warning indicators

### Typography

Themes can modify:
- **Font families**: Primary and secondary fonts
- **Font sizes**: Headings, body text, and UI elements
- **Font weights**: Bold, normal, and light variations
- **Line spacing**: Text readability and layout

### Layout and Spacing

Theme systems include:
- **Spacing scales**: Consistent margins and padding
- **Border radius**: Rounded corners and sharp edges
- **Shadows**: Depth and elevation effects
- **Component sizing**: Button heights, input sizes

## Advanced Theme Management

### Creating Custom Themes

To create your own theme:

1. **Understand Theme Structure**
   - Themes use CSS custom properties (variables)
   - Follow the existing theme patterns
   - Reference the [UI documentation](../ui/README.md)

2. **Create Theme Files**
   ```
   community-themes/your-theme/
   ├── metadata.json    # Theme information
   └── theme.css       # Theme styles
   ```

3. **Define Theme Metadata**
   ```json
   {
     "id": "your-theme",
     "name": "Your Theme Name",
     "author": "Your Name",
     "description": "Theme description",
     "preview": "#color-preview"
   }
   ```

4. **Build and Install**
   - Run `scripts/build_theme_catalog.py`
   - Theme appears in the marketplace
   - Test thoroughly across all components

### Theme Development Best Practices

1. **Accessibility First**
   - Ensure sufficient color contrast
   - Test with screen readers
   - Support high contrast mode

2. **Consistency**
   - Use systematic color schemes
   - Maintain visual hierarchy
   - Follow design system principles

3. **Testing**
   - Test across all UI components
   - Verify theme in different browsers
   - Check mobile responsiveness

### Theme Configuration

Some themes offer configuration options:

1. **Access Theme Settings**
   - Look for theme configuration options
   - May be in theme marketplace or settings

2. **Customize Variables**
   - Adjust color values
   - Modify spacing and sizing
   - Configure font preferences

3. **Save Custom Settings**
   - Apply personalized modifications
   - Create variations of existing themes

## Accessibility Considerations

### High Contrast Support

LibreAssistant includes accessibility features:
- **High Contrast Theme**: Enhanced visibility for users with visual impairments
- **Color Independence**: Information not conveyed by color alone
- **Text Scaling**: Themes work with browser text scaling
- **Focus Indicators**: Clear keyboard navigation indicators

### Screen Reader Compatibility

Themes maintain accessibility:
- **Semantic Structure**: Proper HTML structure preserved
- **ARIA Labels**: Accessibility labels remain functional
- **Focus Management**: Keyboard navigation unaffected
- **Screen Reader Testing**: Regular testing with assistive technologies

## Theme Performance

### Optimization

LibreAssistant themes are optimized for performance:
- **CSS Sanitization**: Themes are processed for safety and performance
- **Minimal Impact**: Theme switching doesn't affect functionality
- **Cached Loading**: Themes are cached for faster switching
- **Progressive Enhancement**: Base functionality works without themes

### Resource Usage

- **Small File Sizes**: Themes use minimal bandwidth
- **Efficient CSS**: Optimized stylesheets
- **No JavaScript**: Themes are pure CSS for security
- **Fast Switching**: Instant theme application

## Troubleshooting Theme Issues

### Common Problems

**Problem**: Theme doesn't apply correctly
- **Solution**: Try refreshing the page
- **Check**: Verify theme is properly installed
- **Alternative**: Switch to a different theme and back

**Problem**: Theme causes display issues
- **Solution**: Switch to a built-in theme
- **Report**: Contact theme author about issues
- **Fallback**: Use High Contrast theme for accessibility

**Problem**: Custom theme not appearing
- **Solution**: Check theme file syntax
- **Verify**: Ensure metadata.json is valid
- **Rebuild**: Run build script again

### Browser Compatibility

LibreAssistant themes work across modern browsers:
- **Chrome/Chromium**: Full support
- **Firefox**: Complete compatibility
- **Safari**: All features supported
- **Edge**: Modern Edge fully supported

## Integration with Other Features

### Plugin Compatibility

Themes work seamlessly with plugins:
- **Plugin UI**: Plugins respect current theme
- **Custom Components**: Plugin components inherit theme styles
- **Marketplace**: Plugin interfaces use theme colors

### Provider Independence

Theme selection is independent of:
- **AI Provider**: Works with any provider
- **Connection Status**: Themes persist across sessions
- **System Health**: Health monitoring respects themes

### Responsive Design

All themes support:
- **Mobile Devices**: Optimized for touch interfaces
- **Tablet Views**: Adaptive layouts
- **Desktop**: Full-featured desktop experience
- **Accessibility**: Screen reader and keyboard navigation

## Theme Feedback System

The theming system provides comprehensive feedback:

![Theme feedback notifications](https://github.com/user-attachments/assets/eca83bb2-282e-4522-a98c-a8265e81714c)

- **Installation Progress**: Real-time installation updates
- **Success Confirmations**: Clear success notifications  
- **Error Handling**: Detailed error messages with solutions
- **Visual Feedback**: Loading indicators and status updates

All theme operations include:
- **Progress Indicators**: Loading spinners during operations
- **Button States**: Disabled states prevent conflicts
- **Status Messages**: Detailed feedback about current operations
- **Immediate Application**: Themes apply instantly upon installation

---

**Next Steps**: With your interface customized, learn about [Reviewing System Health](system-health.md) to monitor LibreAssistant's performance.