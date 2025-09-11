# LibreAssistant Onboarding Guide

This guide walks through LibreAssistant's initial setup process, which helps new users configure their assistant for first use. The onboarding flow consists of 6 steps designed to get you up and running quickly while ensuring you understand how your data will be handled.

## Overview

LibreAssistant's onboarding process guides you through:

1. **Choosing an AI engine** (cloud-based or local models)
2. **Setting up your provider** (API key configuration)
3. **Configuring plugins** (enabling additional capabilities)
4. **Reviewing your configuration** (summary of choices)
5. **Privacy agreement** (understanding data usage)
6. **Setup completion** (final confirmation)

The entire process typically takes 5-10 minutes and can be resumed if interrupted. All settings can be changed later through the settings interface.

## Step-by-Step Walkthrough

### Step 1: Choose AI Engine

**What you'll see:** A dropdown menu asking you to select between cloud-based and local AI services.

**Your options:**
- **Cloud (OpenAI, Anthropic, etc.)**: Uses hosted AI services that offer powerful models but send your data to external providers
- **Local (Ollama, etc.)**: Uses AI models running on your own computer, keeping data private but requiring local setup

**What to choose:**
- Choose **Cloud** if you want access to the most capable models and don't mind your conversations being processed by third-party services
- Choose **Local** if privacy is your top priority and you have or can set up local AI models

**Technical details:** This choice determines which provider adapter LibreAssistant will use to communicate with AI models.

### Step 2: Provider Setup

**What you'll see:** An input field requesting your API key for the selected provider.

**What you need to do:**
- If you chose **Cloud**: Enter your API key from providers like OpenAI, Anthropic, or others
- If you chose **Local**: Enter connection details for your local AI service (usually a local URL)

**Security note:** Your API key is encrypted and stored locally on your device. LibreAssistant never shares your credentials with third parties.

**Where to get API keys:**
- **OpenAI**: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- **Anthropic**: [console.anthropic.com](https://console.anthropic.com)
- **Local setup**: See [Local LLMs with Ollama](../README.md#local-llms-with-ollama) in the main README

### Step 3: Configure Plugins

**What you'll see:** A list of available plugins with toggle switches to enable or disable each one.

**Available plugins may include:**
- **Echo**: Simple message repetition for testing
- **File I/O**: Read and write files on your system
- **Think Tank**: Collaborative idea generation and brainstorming
- **Law**: Search public legislation and government data

**What to consider:**
- Each plugin extends LibreAssistant's capabilities but may access additional data
- Plugins marked as enabled will have access to their respective data sources
- You can review each plugin's description to understand what it does
- Plugin consent can be changed at any time in settings

**Privacy implications:** Enabled plugins may process and access data according to their specific functions. Review each plugin's description to understand what data it accesses.

### Step 4: Review Configuration

**What you'll see:** A summary of all your choices from the previous steps.

**Review items:**
- **AI Provider**: Confirms whether you chose cloud-based or local
- **API Key**: Shows whether an API key was configured (without revealing the actual key)
- **Enabled Plugins**: Lists all plugins you've chosen to enable

**What to do:** Review your selections and ensure they match your preferences. You can use the "Back" button to return to any previous step if you need to make changes.

### Step 5: Privacy Agreement

**What you'll see:** LibreAssistant's privacy policy and data usage terms.

**Key privacy points:**
- **Message handling**: Your messages will be sent to your chosen AI provider
- **Plugin data sharing**: Data will be shared with enabled plugins as needed for their functionality
- **Local storage**: Conversation history is stored locally on your device
- **Third-party sharing**: LibreAssistant never shares your data with third parties without your explicit consent

**What you need to do:** Read the privacy policy and check the agreement box to continue. This step ensures you understand how your data will be handled.

### Step 6: Setup Complete

**What you'll see:** A confirmation screen with a summary of your final configuration.

**Final summary includes:**
- Your chosen AI provider type
- List of enabled plugins
- Confirmation of privacy policy acceptance

**Next steps:** You're now ready to use LibreAssistant! The interface will take you to the main switchboard where you can start conversations and use your configured plugins.

## After Onboarding

### Changing Settings

All onboarding choices can be modified later:

- **Provider settings**: Update API keys or switch providers in Settings
- **Plugin configuration**: Enable/disable plugins in the Plugin Catalogue
- **Theme and appearance**: Customize in the Theme Selector
- **Privacy settings**: Review data handling preferences in Settings

### Getting Help

- **Documentation**: See the main [README.md](../README.md) for usage examples
- **Plugin guides**: Check individual plugin documentation in the `docs/` folder
- **Troubleshooting**: Consult [docs/configuration.md](configuration.md) for common setup issues

## Technical Implementation

### For Developers

The onboarding flow is implemented as a custom web component (`LAOnboardingFlow`) located in `ui/components/onboarding-flow.js`.

**Key technical features:**
- **Accessibility**: Full ARIA support and keyboard navigation
- **Validation**: Step-by-step validation with error handling
- **State management**: Tracks progress and allows backward navigation
- **Event system**: Fires `onboarding-complete` event when finished
- **API integration**: Validates API keys and manages plugin consent

**Testing:** The onboarding flow is covered by tests in:
- `tests/ui/core-flows.test.js` - Functional testing
- `tests/onboarding-flow-test.html` - Interactive testing
- `tests/ui/accessibility-integration.test.js` - Accessibility validation

### Integration Points

The onboarding component integrates with:
- **Provider management**: `/api/v1/providers/{name}/key` for API key storage
- **Plugin system**: `/api/v1/mcp/servers` for plugin discovery and consent
- **Theme system**: Inherits from the current theme CSS variables
- **Main application**: Embedded in the main switchboard interface

### Customization

The onboarding flow can be customized by:
- **Modifying steps**: Edit the step definitions in the component
- **Adding providers**: Extend the provider selection options
- **Plugin integration**: New plugins automatically appear in step 3
- **Styling**: Override CSS custom properties for appearance changes

## Accessibility Features

The onboarding flow includes comprehensive accessibility support:

- **Screen reader compatibility**: Full ARIA labeling and live regions
- **Keyboard navigation**: Complete keyboard-only operation
- **Focus management**: Proper focus handling between steps
- **High contrast support**: Compatible with high-contrast themes
- **Error announcements**: Accessible error messaging

## Browser Compatibility

The onboarding flow requires:
- **Modern browsers**: Support for Custom Elements and Shadow DOM
- **JavaScript enabled**: Required for interactive functionality
- **Local storage**: For saving configuration data
- **Fetch API**: For communicating with the LibreAssistant backend

Tested on current versions of Chrome, Firefox, Safari, and Edge.