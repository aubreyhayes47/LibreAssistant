# LibreAssistant Architecture Documentation

## System Overview

LibreAssistant is a privacy-first, fully local AI assistant built with Flask that provides model management and plugin capabilities through a modern web interface.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     LibreAssistant                         │
├─────────────────────────────────────────────────────────────┤
│  Web Interface (Flask + JavaScript)                        │
│  ┌─────────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │   Templates     │  │ Static Assets│  │  JavaScript   │  │
│  │   - chat.html   │  │ - CSS Styles │  │  - UI Manager │  │
│  │   - index.html  │  │ - Images     │  │  - API Client │  │
│  │   - plugins.html│  │              │  │  - Async Ops  │  │
│  └─────────────────┘  └──────────────┘  └───────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  Core Application Layer                                     │
│  ┌─────────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ Flask App       │  │ LLM Protocol │  │  App Config   │  │
│  │ (ollama_manager)│  │ - JSON Schema│  │  - Environment │  │
│  │ - Routes        │  │ - Validation │  │  - Defaults   │  │
│  │ - API Endpoints │  │ - Error Hand.│  │  - Validation │  │
│  └─────────────────┘  └──────────────┘  └───────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  Plugin System                                              │
│  ┌─────────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ Plugin Loader   │  │ Plugin API   │  │ Usage Tracker │  │
│  │ - Discovery     │  │ - MCP Server │  │ - Activity    │  │
│  │ - Lifecycle     │  │ - Validation │  │ - Monitoring  │  │
│  │ - Management    │  │ - Security   │  │ - Logging     │  │
│  └─────────────────┘  └──────────────┘  └───────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  External Services                                          │
│  ┌─────────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ Ollama Service  │  │ MCP Plugins  │  │  File System  │  │
│  │ - Model Hosting │  │ - External   │  │  - Local Data │  │
│  │ - LLM Interface │  │ - Services   │  │  - Configs    │  │
│  │ - API Calls     │  │ - Sandboxed  │  │  - Logs       │  │
│  └─────────────────┘  └──────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Flask Application (`ollama_manager.py`)

The main Flask application serves as the central hub for:

- **Web Interface**: Serves HTML templates and static assets
- **API Endpoints**: RESTful APIs for frontend communication
- **Route Management**: URL routing and request handling
- **Session Management**: User state and preferences

**Key Responsibilities:**
- Handle HTTP requests/responses
- Coordinate between frontend and backend services
- Manage application state
- Provide API endpoints for all features

### 2. Plugin System

#### Plugin Loader (`plugin_loader.py`)
```
Plugin Discovery Flow:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Scan      │───▶│  Validate   │───▶│   Start     │
│ /plugins    │    │  Manifest   │    │   Server    │
│ Directory   │    │  JSON       │    │   Process   │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Find Plugin │    │ Check       │    │ Register    │
│ Manifests   │    │ Security    │    │ with App    │
│             │    │ Permissions │    │             │
└─────────────┘    └─────────────┘    └─────────────┘
```

#### Plugin API (`plugin_api.py`)
- **MCP Server Protocol**: Communication with external plugin servers
- **Security Validation**: Ensures plugins meet security requirements
- **Sandboxing**: Restricts plugin access to authorized resources

#### Plugin Usage Tracker (`plugin_usage_tracker.py`)
- **Activity Monitoring**: Tracks plugin usage and performance
- **Real-time Updates**: Provides live status information
- **Resource Management**: Monitors resource consumption

### 3. LLM Protocol (`llm_protocol.py`)

#### Protocol Flow
```
User Request → JSON Validation → Plugin Invocation → Response Generation
     │               │                  │                    │
     ▼               ▼                  ▼                    ▼
┌─────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│ Receive │   │   Schema    │   │  Execute    │   │   Format    │
│ Message │   │ Validation  │   │  Plugin     │   │  Response   │
│         │   │             │   │  Actions    │   │             │
└─────────┘   └─────────────┘   └─────────────┘   └─────────────┘
```

**Features:**
- **Structured Communication**: JSON schema-based message format
- **Plugin Integration**: Seamless plugin invocation within LLM responses
- **Error Handling**: Graceful degradation and user-friendly error messages
- **Validation**: Input/output validation for all communications

### 4. Configuration Management (`app_config.py`)

#### Configuration Hierarchy
```
Environment Variables
        ↓
Configuration File
        ↓  
Application Defaults
        ↓
Runtime Configuration
```

**Configuration Categories:**
- **Flask Settings**: Host, port, debug mode
- **Ollama Settings**: Server URL, timeout, model preferences
- **Plugin Settings**: Discovery paths, security policies
- **Security Settings**: CORS, authentication, sandboxing

## Data Flow

### 1. User Interaction Flow
```
Browser ←→ JavaScript ←→ Flask Routes ←→ Core Logic ←→ External Services
   │           │              │             │              │
   ▼           ▼              ▼             ▼              ▼
┌─────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│ UI  │   │ Ajax    │   │ HTTP    │   │ Python  │   │ Ollama  │
│ DOM │   │ API     │   │ API     │   │ Logic   │   │ Plugin  │
│     │   │ Calls   │   │ Routes  │   │         │   │ Servers │
└─────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘
```

### 2. Plugin Communication Flow
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    LLM      │───▶│   Plugin    │───▶│   External  │
│  Protocol   │    │   Loader    │    │   Service   │
│             │    │             │    │   (MCP)     │
└─────────────┘    └─────────────┘    └─────────────┘
       ▲                   │                   │
       │                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Response  │◀───│   Usage     │◀───│   Plugin    │
│  Processing │    │  Tracker    │    │  Response   │
│             │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘
```

## Security Model

### 1. Plugin Security
```
┌─────────────────────────────────────────────────────────┐
│                 Security Layers                         │
├─────────────────────────────────────────────────────────┤
│ 1. Manifest Validation                                  │
│    - Schema compliance                                  │
│    - Permission declarations                            │
│    - Security policy adherence                         │
├─────────────────────────────────────────────────────────┤
│ 2. Sandboxing                                          │
│    - Process isolation                                  │
│    - File system restrictions                          │
│    - Network access controls                           │
├─────────────────────────────────────────────────────────┤
│ 3. Runtime Monitoring                                  │
│    - Resource usage tracking                           │
│    - Activity logging                                  │
│    - Anomaly detection                                 │
├─────────────────────────────────────────────────────────┤
│ 4. User Consent                                        │
│    - Explicit permission requests                      │
│    - Granular access controls                          │
│    - Audit trails                                      │
└─────────────────────────────────────────────────────────┘
```

### 2. Data Protection
- **Local Processing**: All data processing happens locally
- **No Cloud Dependencies**: Core functionality works offline
- **Explicit Consent**: Users control all data sharing
- **Audit Logging**: All plugin activities are logged

## API Design

### REST API Endpoints
```
GET  /                    - Main application interface
GET  /models             - List available models
POST /models             - Interact with models
GET  /plugins            - Plugin management interface
GET  /api/plugins        - Plugin discovery API
POST /api/plugins/{id}   - Plugin control operations
GET  /monitoring         - System monitoring interface
GET  /settings           - Configuration interface
```

### WebSocket Integration (Future)
```
/ws/chat       - Real-time chat communication
/ws/plugins    - Live plugin status updates
/ws/monitoring - Real-time system metrics
```

## Performance Considerations

### 1. Asynchronous Operations
- **Non-blocking UI**: All long-running operations are asynchronous
- **Progress Feedback**: Real-time status updates for operations
- **Queue Management**: Operation prioritization and scheduling

### 2. Resource Management
- **Plugin Lifecycle**: Efficient start/stop of plugin servers
- **Memory Management**: Monitoring and cleanup of resources
- **Connection Pooling**: Efficient communication with external services

### 3. Caching Strategy
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Browser   │    │   Flask     │    │  External   │
│   Cache     │    │   Cache     │    │  Service    │
│  (Static)   │    │ (Dynamic)   │    │   Cache     │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
   Static Assets     Session Data        API Responses
   CSS, JS, Images   User Preferences    Model Data
```

## Deployment Architecture

### Development Mode
```
┌─────────────────────────────────────────────────────────┐
│ Local Development Environment                           │
├─────────────────────────────────────────────────────────┤
│ Flask Development Server                                │
│ - Debug mode enabled                                    │
│ - Hot reloading                                         │
│ - Detailed error pages                                  │
├─────────────────────────────────────────────────────────┤
│ Local Ollama Instance                                   │
│ - http://localhost:11434                               │
│ - Direct model access                                   │
├─────────────────────────────────────────────────────────┤
│ Plugin Servers (Local)                                 │
│ - Auto-start on application launch                     │
│ - Local file system access                             │
│ - Development tools integration                        │
└─────────────────────────────────────────────────────────┘
```

### Production Mode
```
┌─────────────────────────────────────────────────────────┐
│ Production Environment                                   │
├─────────────────────────────────────────────────────────┤
│ WSGI Server (Gunicorn/uWSGI)                           │
│ - Process management                                    │
│ - Load balancing                                        │
│ - Error handling                                        │
├─────────────────────────────────────────────────────────┤
│ Reverse Proxy (Nginx)                                  │
│ - Static file serving                                   │
│ - SSL termination                                       │
│ - Request routing                                       │
├─────────────────────────────────────────────────────────┤
│ Containerized Deployment                               │
│ - Docker containers                                     │
│ - Service isolation                                     │
│ - Orchestration ready                                   │
└─────────────────────────────────────────────────────────┘
```

## Future Architecture Considerations

### 1. Scalability
- **Microservices**: Split into smaller, focused services
- **Event-Driven**: Implement event-driven architecture
- **Database Integration**: Add persistent storage options

### 2. Enhanced Security
- **Authentication**: User authentication and authorization
- **Encryption**: Data encryption at rest and in transit
- **Audit System**: Comprehensive audit logging

### 3. Cloud Integration (Optional)
- **Hybrid Mode**: Local processing with optional cloud features
- **Federated Learning**: Privacy-preserving model improvements
- **Backup Services**: Secure configuration and data backup

## Development Guidelines

### 1. Code Organization
- **Modular Design**: Separate concerns into focused modules
- **Clear Interfaces**: Well-defined APIs between components
- **Documentation**: Comprehensive inline and external documentation

### 2. Testing Strategy
- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- **E2E Tests**: Test complete user workflows
- **Security Tests**: Validate security controls

### 3. Monitoring and Observability
- **Logging**: Structured logging with appropriate levels
- **Metrics**: Key performance and business metrics
- **Tracing**: Request tracing for debugging
- **Health Checks**: Application and dependency health monitoring

## Conclusion

LibreAssistant's architecture prioritizes:
- **Privacy**: Local-first processing with explicit user control
- **Extensibility**: Plugin system for easy feature additions
- **Security**: Multi-layered security controls and validation
- **Usability**: Intuitive interface with clear feedback
- **Maintainability**: Clean code structure with comprehensive testing

This architecture supports the project's goals of providing a powerful, private, and user-friendly AI assistant while maintaining flexibility for future enhancements.