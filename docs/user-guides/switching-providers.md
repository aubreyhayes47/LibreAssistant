# 🔄 Switching AI Providers

LibreAssistant allows you to switch between different AI providers seamlessly. You can connect to cloud-based services like OpenAI or use local models running on your machine.

## Overview

LibreAssistant supports multiple AI provider types:
- **Cloud Providers**: OpenAI, Anthropic, and other cloud-based services
- **Local Providers**: Models running locally on your machine
- **Custom Endpoints**: Your own AI service endpoints

## Step-by-Step Guide

### 1. Access the Provider Selector

The provider selector is available in multiple locations throughout LibreAssistant:

**Option A: From the Main Interface**
- Navigate to the main LibreAssistant interface
- Look for the **Provider** section in the top navigation area
- You'll see the current provider status and a dropdown menu

**Option B: From the Settings Tab**
- Click on the **Switchboard** tab in the main navigation
- Find the provider selector in the main workspace area

![Provider switching interface](https://github.com/user-attachments/assets/4280a33c-9e83-4858-b06b-438a12c24af7)

### 2. Understanding Provider Status Indicators

Before switching providers, it's important to understand the status indicators:

- 🟢 **Green dot**: Connected and working properly
- 🔴 **Red dot**: Connection error or provider unavailable  
- 🟡 **Yellow dot**: Loading or connecting
- ⚪ **Gray dot**: Disconnected or not configured

### 3. Switch to a Different Provider

1. **Click the Provider Dropdown**
   - Click on the provider dropdown menu
   - You'll see a list of available providers

2. **Select Your Desired Provider**
   - Choose from the available options:
     - Cloud (OpenAI)
     - Local Model
     - (Additional providers may be available depending on your configuration)

3. **Monitor the Switch Process**
   - After selecting a provider, you'll see a loading indicator
   - The system will display "Switching to [Provider Name]..." 
   - Wait for the connection to complete

4. **Verify the Switch**
   - Once successful, you'll see "Successfully switched to [Provider Name]"
   - The status indicator will turn green
   - The dropdown will show your newly selected provider

### 4. Handling Connection Errors

If a provider switch fails, you'll see an error message. Common issues and solutions:

**"Connection failed" or "HTTP 500" errors:**
- Check your internet connection
- Verify your API credentials are correct
- Ensure the provider service is available

**"Provider unavailable" errors:**
- The provider service may be down
- Try switching to an alternative provider
- Check the system health monitor for more details

**"Authentication failed" errors:**
- Verify your API key is correctly configured
- Check that your account has sufficient credits/access
- Ensure your API key hasn't expired

### 5. Testing Your Provider Connection

After switching providers, it's recommended to test the connection:

1. **Send a Test Request**
   - Type a simple question in the request field
   - Click "Send request"
   - Verify you receive a response

2. **Check Response Quality**
   - Ensure the response is relevant and complete
   - Verify the response time is acceptable

## Advanced Configuration

### Setting Up Local Providers

To use local AI models:

1. **Install Required Dependencies**
   - Ensure you have the appropriate model files
   - Install any required runtime dependencies

2. **Configure Local Model Path**
   - Set up your local model endpoint
   - Configure any required authentication

3. **Test Local Connection**
   - Switch to "Local Model" in the provider dropdown
   - Send a test request to verify functionality

### Provider-Specific Settings

Different providers may have unique configuration options:

- **Response length limits**
- **Model selection** (GPT-3.5, GPT-4, etc.)
- **Temperature and creativity settings**
- **Custom API endpoints**

Access these settings through the provider configuration interface.

## Troubleshooting

### Common Issues

**Problem**: Provider switch gets stuck on "Loading..."
- **Solution**: Refresh the page and try again
- **Alternative**: Check your network connection

**Problem**: New provider shows as connected but doesn't respond
- **Solution**: Send a test request to verify the connection
- **Alternative**: Switch back to a known working provider

**Problem**: Frequent disconnections
- **Solution**: Check system health for network issues
- **Alternative**: Contact your provider's support team

### Getting Help

- **System Health**: Check the [System Health guide](system-health.md) for connection diagnostics
- **API Documentation**: See the [API documentation](../api.md) for technical details
- **Provider Documentation**: Consult your AI provider's documentation for specific configuration requirements

## Best Practices

1. **Keep Multiple Providers Configured**: Have backup providers configured in case your primary provider is unavailable

2. **Monitor Provider Performance**: Use the system health monitor to track response times and reliability

3. **Test After Configuration Changes**: Always send a test request after switching providers

4. **Monitor API Usage**: Keep track of your usage to avoid exceeding limits

5. **Stay Updated**: Check for provider updates and new configuration options regularly

## Feedback and Notifications

LibreAssistant provides comprehensive feedback during provider operations:

- **Progress indicators** show the current state of operations
- **Success notifications** confirm when operations complete
- **Error notifications** provide detailed information about failures
- **Status updates** keep you informed of the current provider state

All notifications appear in the notification area and provide actionable information to help you resolve any issues quickly.

---

**Next Steps**: Once you have your AI provider configured, you may want to explore [Installing and Managing Plugins](installing-plugins.md) to extend LibreAssistant's functionality.