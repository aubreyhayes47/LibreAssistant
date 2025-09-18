# MCP Plugin Auto-Start Feature

## Overview

LibreAssistant now automatically starts all MCP (Model Context Protocol) plugin servers when you run `python main.py`. This eliminates the need to manually start each plugin server individually.

## How It Works

When you start the LibreAssistant Flask application:

1. **Plugin Discovery**: The system automatically discovers all plugins in the `plugins/` directory
2. **Permission Auto-Approval**: All required permissions are automatically granted to plugins during startup  
3. **Sequential Startup**: Plugins are started one by one with a small delay to avoid port conflicts
4. **Error Logging**: Any startup failures are logged with detailed error information
5. **Graceful Shutdown**: All plugin processes are automatically stopped when the main app is terminated

## Usage

### Normal Startup (with auto-start)
```bash
python main.py
```

### Disable Auto-Start
If you want to start plugins manually, you can disable auto-start by setting an environment variable:

```bash
# Any of these values will disable auto-start:
DISABLE_PLUGIN_AUTOSTART=true python main.py
DISABLE_PLUGIN_AUTOSTART=1 python main.py  
DISABLE_PLUGIN_AUTOSTART=yes python main.py
```

## Example Output

```
[AutoStart] Found 4 plugins, auto-approving permissions and starting them...
[AutoStart] Auto-approved permissions for local-fileio: {'file:read', 'file:write', 'file:delete', 'file:list'}
[AutoStart] Auto-approved permissions for brave-search: {'network'}
[AutoStart] Auto-approved permissions for courtlistener: {'network'}
[AutoStart] Starting plugin: Local File I/O (local-fileio)
[AutoStart] ✓ Successfully started Local File I/O on port 5101
[AutoStart] Starting plugin: Test Plugin (test-plugin)
[AutoStart] ✓ Successfully started Test Plugin on port 5199
[AutoStart] Starting plugin: Brave Search (brave-search)
[AutoStart] ✓ Successfully started Brave Search on port 5103
[AutoStart] Starting plugin: CourtListener (courtlistener)
[AutoStart] ✓ Successfully started CourtListener on port 5102
[AutoStart] Plugin startup complete: 4 started, 0 failed
[Main] Starting Flask application...
```

## Error Handling

- **Startup Failures**: If a plugin fails to start, the error is logged but doesn't prevent other plugins or the main app from starting
- **Permission Issues**: Plugins requiring special permissions are automatically approved during auto-start
- **Port Conflicts**: Small delays between plugin starts help avoid port binding conflicts
- **Graceful Shutdown**: Signal handlers ensure all plugins are properly stopped when the app is terminated

## Manual Plugin Control

Even with auto-start enabled, you can still manually control plugins through the web interface or API:

- **API Endpoint**: `GET /api/plugin/status` - Check plugin status
- **API Endpoint**: `POST /api/plugin/enable` - Manually start a plugin  
- **API Endpoint**: `POST /api/plugin/disable` - Manually stop a plugin

## Technical Details

- **Signal Handling**: The app responds to SIGINT (Ctrl+C) and SIGTERM signals for graceful shutdown
- **Process Management**: Plugin processes are managed using Python's `subprocess.Popen`
- **Monitoring**: Each plugin process is monitored in a separate thread for crash detection
- **File Handles**: Log file handles are properly managed to avoid resource leaks

## Troubleshooting

### Plugin Won't Start
1. Check plugin logs in `plugins/{plugin-name}/logs/`
2. Verify the plugin's `plugin-manifest.json` is valid
3. Ensure the plugin's entrypoint command is correct
4. Check for port conflicts with other services

### Auto-Start Not Working
1. Verify you don't have `DISABLE_PLUGIN_AUTOSTART` set
2. Check that plugins exist in the `plugins/` directory
3. Look for error messages in the console output

### Graceful Shutdown Issues
The app should automatically stop all plugins when terminated. If plugins remain running:
1. Use the API to manually stop them: `POST /api/plugin/disable`
2. Check for zombie processes: `ps aux | grep python`