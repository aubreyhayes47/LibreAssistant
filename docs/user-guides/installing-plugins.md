# 🔌 Installing and Managing Plugins

LibreAssistant's plugin system allows you to extend functionality with specialized tools. Plugins can add capabilities like file processing, data analysis, web searches, and much more.

## Overview

LibreAssistant supports various types of plugins:
- **Built-in Plugins**: Core plugins included with LibreAssistant
- **Community Plugins**: Third-party plugins from the community
- **Custom Plugins**: Plugins you develop or install manually

### Available Built-in Plugins

- **[Echo Plugin](../echo_plugin.md)**: Repeat and process messages
- **[File I/O Plugin](../file_io_plugin.md)**: Read and write files
- **[Think Tank Plugin](../think_tank_plugin.md)**: Collaborative idea generation
- **[Law Plugin](../law_api.md)**: Search public legislation

## Step-by-Step Guide

### 1. Access the Plugin Catalogue

The plugin management interface is available through the main navigation:

1. **Navigate to Plugin Catalogue**
   - Click on the **Catalogue** tab in the main navigation
   - You'll see the plugin management interface

2. **View Available Plugins**
   - The catalogue shows all available plugins
   - Each plugin displays its name, status, and description

![Plugin management interface](https://github.com/user-attachments/assets/e74920d3-815d-4dc2-893d-d49c978e1dff)

### 2. Understanding Plugin Status

Plugins can have different states:
- ✅ **Enabled**: Plugin is active and ready to use
- ❌ **Disabled**: Plugin is installed but not active
- ⚠️ **Error**: Plugin has encountered an issue
- 🔄 **Loading**: Plugin is being enabled/disabled

### 3. Enabling a Plugin

To activate a plugin that's currently disabled:

1. **Locate the Plugin**
   - Find the plugin you want to enable in the catalogue
   - Check its current status

2. **Click the Enable Toggle**
   - Click the checkbox or toggle button next to the plugin
   - The interface will show "Enabling..." status

3. **Monitor the Process**
   - You'll see loading indicators and progress messages
   - The system displays "Enabling plugin [plugin_name]..."
   - Status updates appear in real-time

4. **Confirm Success**
   - Once enabled, you'll see "Plugin [plugin_name] enabled successfully"
   - The status changes to "Enabled"
   - The plugin is now available for use

![Plugin enabling process](https://github.com/user-attachments/assets/4280a33c-9e83-4858-b06b-438a12c24af7)

### 4. Disabling a Plugin

To deactivate a plugin:

1. **Find the Active Plugin**
   - Locate the plugin in the catalogue
   - Verify it shows as "Enabled"

2. **Toggle Off**
   - Click the enabled checkbox/toggle to disable
   - Confirm the action if prompted

3. **Wait for Completion**
   - The system will show "Disabling plugin [plugin_name]..."
   - Progress indicators will update you on the status

4. **Verify Deactivation**
   - Success message: "Plugin [plugin_name] disabled successfully"
   - Status changes to "Disabled"

### 5. Using Plugins in Requests

Once plugins are enabled, you can use them in your requests:

1. **Access Plugin Selection**
   - In the main request interface, look for the plugin dropdown
   - It's typically located near the send button

2. **Select a Plugin**
   - Click the plugin dropdown menu
   - Choose from available enabled plugins
   - Select "No plugin" if you don't want to use one

3. **Send Plugin-Enhanced Requests**
   - Type your request in the text field
   - Ensure your desired plugin is selected
   - Click "Send request"

4. **Review Plugin Output**
   - The response will include plugin-specific functionality
   - Plugin results are integrated into the main response

## Advanced Plugin Management

### Installing Community Plugins

1. **Browse Community Plugins**
   - Visit the community plugin repository
   - Review plugin descriptions and ratings
   - Check compatibility with your LibreAssistant version

2. **Download Plugin Files**
   - Download the plugin package
   - Verify the plugin's authenticity and safety

3. **Install Plugin**
   - Place plugin files in the appropriate directory
   - Restart LibreAssistant if required
   - The plugin should appear in your catalogue

### Plugin Configuration

Some plugins offer configuration options:

1. **Access Plugin Settings**
   - Look for a settings or configuration icon next to the plugin
   - Click to open the configuration interface

2. **Adjust Settings**
   - Modify plugin-specific options
   - Set API keys or endpoints if required
   - Configure behavior preferences

3. **Save Configuration**
   - Apply your changes
   - Test the plugin to ensure proper configuration

### Plugin Dependencies

Some plugins require additional setup:

- **API Keys**: Some plugins need external service credentials
- **Network Access**: Plugins may need internet connectivity
- **File Permissions**: File-related plugins need appropriate access
- **External Tools**: Some plugins depend on system utilities

## Troubleshooting Plugin Issues

### Common Problems and Solutions

**Problem**: Plugin won't enable
- **Check Dependencies**: Ensure all required dependencies are installed
- **Verify Permissions**: Check that LibreAssistant has necessary permissions
- **Review Logs**: Check system health for error details
- **Restart Application**: Sometimes a restart resolves temporary issues

**Problem**: Plugin shows "Error" status
- **Check Configuration**: Verify plugin settings are correct
- **Test Network**: Ensure network-dependent plugins can connect
- **Update Plugin**: Check for plugin updates
- **Reinstall**: Remove and reinstall the problematic plugin

**Problem**: Plugin works but gives unexpected results
- **Review Documentation**: Check the plugin's specific documentation
- **Verify Input Format**: Ensure your requests match expected formats
- **Check Configuration**: Review plugin-specific settings
- **Test with Simple Requests**: Start with basic requests to isolate issues

### Error Messages and Solutions

**"Failed to enable plugin: HTTP 500"**
- Server error - check system health
- May indicate backend service issues
- Try again later or contact support

**"Plugin dependency not found"**
- Missing required software or libraries
- Install necessary dependencies
- Check plugin documentation for requirements

**"Authentication failed"**
- Incorrect API keys or credentials
- Verify authentication settings
- Check with the external service provider

## Plugin Security and Safety

### Best Practices

1. **Verify Plugin Sources**
   - Only install plugins from trusted sources
   - Review plugin code if possible
   - Check community ratings and reviews

2. **Monitor Plugin Behavior**
   - Watch for unexpected network activity
   - Monitor file system access
   - Review plugin output for anomalies

3. **Regular Updates**
   - Keep plugins updated to latest versions
   - Review update notes for security fixes
   - Remove unused or deprecated plugins

4. **Permission Management**
   - Grant minimal necessary permissions
   - Review plugin access requests
   - Regularly audit plugin permissions

## Plugin Development

### Creating Custom Plugins

If you want to develop your own plugins:

1. **Review Documentation**
   - Study the [Plugin API documentation](../plugin-api.md)
   - Understand the plugin architecture
   - Review example plugins

2. **Development Setup**
   - Set up development environment
   - Use plugin templates or scaffolding tools
   - Test in development mode

3. **Testing and Validation**
   - Test plugin functionality thoroughly
   - Validate security considerations
   - Ensure compatibility with LibreAssistant versions

4. **Distribution**
   - Package plugin appropriately
   - Provide clear documentation
   - Consider contributing to the community

## Feedback and Monitoring

The plugin system provides comprehensive feedback:

- **Real-time Status Updates**: See exactly what's happening during operations
- **Success Notifications**: Clear confirmation when actions complete
- **Error Details**: Specific information about failures
- **Progress Indicators**: Visual feedback during longer operations

![Plugin feedback system](https://github.com/user-attachments/assets/eca83bb2-282e-4522-a98c-a8265e81714c)

All plugin operations include:
- Loading spinners during processing
- Disabled states to prevent conflicts
- Detailed progress messages
- Clear success/error notifications

## Integration with Other Features

Plugins work seamlessly with other LibreAssistant features:

- **Provider Independence**: Plugins work with any AI provider
- **Theme Compatibility**: Plugin interfaces respect your theme selection
- **System Health**: Plugin status is monitored in system health
- **Request History**: Plugin-enhanced requests are saved in history

---

**Next Steps**: With plugins configured, explore [Changing Themes](changing-themes.md) to customize your LibreAssistant appearance.