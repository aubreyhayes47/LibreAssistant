# LibreAssistant API Documentation

## Overview

LibreAssistant provides a comprehensive REST API for managing models, plugins, and chat interactions. This document covers all available endpoints with examples and usage patterns.

## Base URL

```
http://localhost:5000
```

## Authentication

Currently, LibreAssistant operates without authentication for local usage. All API endpoints are accessible without credentials.

## API Endpoints

### 1. Application Interface

#### GET `/`
Returns the main application interface.

**Response:**
- Content-Type: `text/html`
- Status: `200 OK`

```http
GET / HTTP/1.1
Host: localhost:5000

HTTP/1.1 200 OK
Content-Type: text/html
```

### 2. Model Management

#### GET `/models`
Retrieve list of available Ollama models.

**Response Format:**
```json
{
  "models": [
    {
      "name": "llama2:latest",
      "size": "3.8GB",
      "modified_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

**Example:**
```bash
curl -X GET http://localhost:5000/models
```

**Possible Status Codes:**
- `200`: Success
- `500`: Ollama service unavailable
- `504`: Request timeout

#### POST `/models`
Interact with a model (send chat message).

**Request Format:**
```json
{
  "model": "llama2:latest",
  "message": "Hello, how are you?",
  "enable_plugins": true,
  "stream": false
}
```

**Response Format:**
```json
{
  "response": "Hello! I'm doing well, thank you for asking.",
  "model": "llama2:latest",
  "created_at": "2024-01-15T10:30:00Z",
  "plugins_used": []
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/models \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama2:latest", 
    "message": "What is the weather like?",
    "enable_plugins": true
  }'
```

**Possible Status Codes:**
- `200`: Success
- `400`: Invalid request format
- `500`: Model interaction failed

### 3. Plugin Management

#### GET `/plugins`
Returns the plugin management interface.

**Response:**
- Content-Type: `text/html`
- Status: `200 OK`

#### GET `/api/plugins`
Retrieve list of available plugins.

**Response Format:**
```json
{
  "plugins": [
    {
      "id": "local-fileio",
      "name": "Local File I/O",
      "version": "1.0.0",
      "description": "Securely read, write, list, and delete files",
      "status": "running",
      "port": 5101,
      "permissions": ["file:read", "file:write"],
      "config": {
        "base_directory": "/path/to/files"
      }
    }
  ]
}
```

**Example:**
```bash
curl -X GET http://localhost:5000/api/plugins
```

**Possible Status Codes:**
- `200`: Success
- `500`: Plugin discovery failed

#### POST `/api/plugins/{plugin_id}/start`
Start a specific plugin.

**Path Parameters:**
- `plugin_id`: The unique identifier of the plugin

**Request Format:**
```json
{
  "config": {
    "base_directory": "/custom/path"
  }
}
```

**Response Format:**
```json
{
  "success": true,
  "message": "Plugin started successfully",
  "plugin": {
    "id": "local-fileio",
    "status": "running",
    "port": 5101
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/plugins/local-fileio/start \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "base_directory": "/home/user/documents"
    }
  }'
```

#### POST `/api/plugins/{plugin_id}/stop`
Stop a specific plugin.

**Response Format:**
```json
{
  "success": true,
  "message": "Plugin stopped successfully",
  "plugin": {
    "id": "local-fileio",
    "status": "stopped"
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/plugins/local-fileio/stop
```

#### GET `/api/plugins/{plugin_id}/status`
Get status of a specific plugin.

**Response Format:**
```json
{
  "id": "local-fileio",
  "name": "Local File I/O",
  "status": "running",
  "port": 5101,
  "uptime": "2h 35m",
  "last_activity": "2024-01-15T10:30:00Z",
  "resource_usage": {
    "memory": "45MB",
    "cpu": "2.1%"
  }
}
```

#### POST `/api/plugins/{plugin_id}/configure`
Update plugin configuration.

**Request Format:**
```json
{
  "config": {
    "base_directory": "/new/path",
    "max_file_size": "10MB"
  }
}
```

**Response Format:**
```json
{
  "success": true,
  "message": "Plugin configured successfully",
  "config": {
    "base_directory": "/new/path",
    "max_file_size": "10MB"
  }
}
```

### 4. System Monitoring

#### GET `/monitoring`
Returns the system monitoring interface.

#### GET `/api/system/health`
Get system health status.

**Response Format:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "ollama": {
      "status": "connected",
      "response_time": "245ms"
    },
    "plugins": {
      "total": 3,
      "running": 2,
      "stopped": 1
    }
  },
  "resources": {
    "memory_usage": "512MB",
    "cpu_usage": "15%",
    "disk_space": "2.3GB available"
  }
}
```

**Example:**
```bash
curl -X GET http://localhost:5000/api/system/health
```

#### GET `/api/system/logs`
Retrieve system logs.

**Query Parameters:**
- `level` (optional): Filter by log level (debug, info, warning, error)
- `limit` (optional): Maximum number of entries (default: 100)
- `since` (optional): ISO timestamp to filter logs from

**Response Format:**
```json
{
  "logs": [
    {
      "timestamp": "2024-01-15T10:30:00Z",
      "level": "info",
      "message": "Plugin local-fileio started successfully",
      "component": "plugin_loader"
    }
  ],
  "total": 150,
  "filtered": 25
}
```

**Example:**
```bash
curl -X GET "http://localhost:5000/api/system/logs?level=error&limit=50"
```

### 5. Configuration

#### GET `/settings`
Returns the configuration interface.

#### GET `/api/config`
Get current application configuration.

**Response Format:**
```json
{
  "app": {
    "name": "LibreAssistant",
    "version": "1.0.0",
    "debug": false
  },
  "ollama": {
    "host": "http://localhost:11434",
    "timeout": 180
  },
  "plugins": {
    "auto_start": true,
    "base_port": 5100
  }
}
```

#### POST `/api/config`
Update application configuration.

**Request Format:**
```json
{
  "ollama": {
    "host": "http://custom-ollama:11434",
    "timeout": 300
  },
  "plugins": {
    "auto_start": false
  }
}
```

**Response Format:**
```json
{
  "success": true,
  "message": "Configuration updated successfully",
  "config": {
    "ollama": {
      "host": "http://custom-ollama:11434",
      "timeout": 300
    }
  }
}
```

## LLM Protocol JSON Schema

### Request Schema

```json
{
  "type": "object",
  "properties": {
    "model": {
      "type": "string",
      "description": "The Ollama model to use"
    },
    "message": {
      "type": "string", 
      "description": "The user's message"
    },
    "enable_plugins": {
      "type": "boolean",
      "default": true,
      "description": "Whether to enable plugin support"
    },
    "stream": {
      "type": "boolean",
      "default": false,
      "description": "Whether to stream the response"
    },
    "context": {
      "type": "array",
      "items": {
        "type": "object"
      },
      "description": "Previous conversation context"
    }
  },
  "required": ["model", "message"]
}
```

### Response Schema

#### Message Response
```json
{
  "type": "object",
  "properties": {
    "action": {
      "type": "string",
      "enum": ["message"]
    },
    "content": {
      "type": "object",
      "properties": {
        "text": {
          "type": "string",
          "description": "The response text"
        },
        "markdown": {
          "type": "boolean",
          "default": false,
          "description": "Whether the text contains markdown"
        }
      },
      "required": ["text"]
    }
  },
  "required": ["action", "content"]
}
```

#### Plugin Invocation Response
```json
{
  "type": "object",
  "properties": {
    "action": {
      "type": "string", 
      "enum": ["plugin_invoke"]
    },
    "content": {
      "type": "object",
      "properties": {
        "plugin": {
          "type": "string",
          "description": "Plugin identifier"
        },
        "input": {
          "type": "object",
          "description": "Plugin input parameters"
        },
        "reason": {
          "type": "string",
          "description": "Why the plugin is being invoked"
        }
      },
      "required": ["plugin", "input", "reason"]
    }
  },
  "required": ["action", "content"]
}
```

## Error Handling

### Standard Error Response
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "User-friendly error message",
    "details": "Technical details for debugging",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### Common Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `VALIDATION_ERROR` | Request validation failed | 400 |
| `MODEL_NOT_FOUND` | Specified model not available | 404 |
| `PLUGIN_NOT_FOUND` | Plugin not found | 404 |
| `PLUGIN_START_FAILED` | Plugin failed to start | 500 |
| `OLLAMA_UNAVAILABLE` | Ollama service unavailable | 503 |
| `TIMEOUT_ERROR` | Request timed out | 504 |
| `INTERNAL_ERROR` | Unexpected server error | 500 |

## Rate Limiting

Currently, LibreAssistant does not implement rate limiting for local usage. In production deployments, consider implementing rate limiting based on:

- Requests per minute per IP
- Model interaction frequency
- Plugin operation limits

## API Client Examples

### Python Client
```python
import requests
import json

class LibreAssistantClient:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
    
    def chat(self, model, message, enable_plugins=True):
        """Send a chat message to a model"""
        response = requests.post(
            f"{self.base_url}/models",
            json={
                "model": model,
                "message": message,
                "enable_plugins": enable_plugins
            }
        )
        return response.json()
    
    def get_plugins(self):
        """Get list of available plugins"""
        response = requests.get(f"{self.base_url}/api/plugins")
        return response.json()
    
    def start_plugin(self, plugin_id, config=None):
        """Start a plugin with optional configuration"""
        data = {"config": config} if config else {}
        response = requests.post(
            f"{self.base_url}/api/plugins/{plugin_id}/start",
            json=data
        )
        return response.json()

# Usage example
client = LibreAssistantClient()
result = client.chat("llama2:latest", "Hello, world!")
print(result["response"])
```

### JavaScript Client
```javascript
class LibreAssistantClient {
    constructor(baseUrl = 'http://localhost:5000') {
        this.baseUrl = baseUrl;
    }
    
    async chat(model, message, enablePlugins = true) {
        const response = await fetch(`${this.baseUrl}/models`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                model,
                message,
                enable_plugins: enablePlugins
            })
        });
        return await response.json();
    }
    
    async getPlugins() {
        const response = await fetch(`${this.baseUrl}/api/plugins`);
        return await response.json();
    }
    
    async startPlugin(pluginId, config = null) {
        const response = await fetch(`${this.baseUrl}/api/plugins/${pluginId}/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ config })
        });
        return await response.json();
    }
}

// Usage example
const client = new LibreAssistantClient();
client.chat('llama2:latest', 'Hello, world!')
    .then(result => console.log(result.response));
```

### cURL Examples

#### Basic Chat
```bash
curl -X POST http://localhost:5000/models \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama2:latest",
    "message": "Explain quantum computing",
    "enable_plugins": true
  }'
```

#### Plugin Management
```bash
# List plugins
curl -X GET http://localhost:5000/api/plugins

# Start a plugin
curl -X POST http://localhost:5000/api/plugins/local-fileio/start \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "base_directory": "/home/user/documents"
    }
  }'

# Check plugin status
curl -X GET http://localhost:5000/api/plugins/local-fileio/status
```

## Testing the API

### Health Check
```bash
curl -X GET http://localhost:5000/api/system/health
```

### Model List
```bash
curl -X GET http://localhost:5000/models
```

### Plugin Discovery
```bash
curl -X GET http://localhost:5000/api/plugins
```

## Best Practices

### 1. Request Handling
- Always include appropriate `Content-Type` headers
- Handle HTTP status codes properly
- Implement retry logic for transient failures
- Use appropriate timeouts for long-running operations

### 2. Error Handling
- Check for error responses and handle them gracefully
- Log errors for debugging purposes
- Provide user-friendly error messages
- Implement fallback behavior when possible

### 3. Plugin Integration
- Check plugin availability before invoking
- Handle plugin failures gracefully
- Monitor plugin resource usage
- Implement proper cleanup on shutdown

### 4. Security Considerations
- Validate all input data
- Sanitize file paths and user input
- Monitor for unusual API usage patterns
- Implement proper authentication in production

## Future API Enhancements

### Planned Features
- **WebSocket Support**: Real-time bidirectional communication
- **API Versioning**: Support for multiple API versions
- **Bulk Operations**: Batch operations for efficiency
- **Webhooks**: Event notifications for external systems
- **GraphQL Endpoint**: Alternative query interface
- **API Documentation UI**: Interactive API explorer

### Authentication & Authorization
- **JWT Tokens**: Secure API access
- **Role-Based Access**: Different permission levels
- **API Keys**: Machine-to-machine authentication
- **OAuth Integration**: Third-party authentication

This API documentation provides comprehensive coverage of LibreAssistant's capabilities, enabling developers to build powerful integrations and applications on top of the platform.