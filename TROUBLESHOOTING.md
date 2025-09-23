# LibreAssistant Troubleshooting Guide

## Quick Diagnosis

### Is LibreAssistant Working?
Run this quick checklist to identify the problem area:

1. **Application Starts**: ✅ LibreAssistant launches without errors
2. **Ollama Connection**: ✅ Can see models in the Models tab
3. **Basic Chat**: ✅ Can send messages and get responses
4. **Plugin Discovery**: ✅ Plugins appear in Plugin Catalogue
5. **Plugin Functionality**: ✅ Can enable and use plugins

If any step fails, jump to the relevant section below.

## Application Startup Issues

### Problem: LibreAssistant Won't Start

#### Error: "ModuleNotFoundError" or "ImportError"
**Cause**: Missing Python dependencies

**Solution**:
```bash
# Navigate to LibreAssistant directory
cd /path/to/LibreAssistant

# Install dependencies
pip install -r requirements.txt

# Or with specific Python version
python3 -m pip install -r requirements.txt
```

#### Error: "Port already in use" or "Address already in use"
**Cause**: Another application is using port 5000

**Solutions**:
1. **Find the conflicting process**:
   ```bash
   # On Linux/macOS
   lsof -i :5000
   
   # On Windows
   netstat -ano | findstr :5000
   ```

2. **Use a different port**:
   ```bash
   export FLASK_PORT=5001
   python main.py
   ```

3. **Stop the conflicting service**:
   ```bash
   # If it's another LibreAssistant instance
   pkill -f "python main.py"
   ```

#### Error: "Permission denied" when starting
**Cause**: Insufficient permissions or restricted port

**Solutions**:
1. **Run with appropriate permissions**:
   ```bash
   # Don't use sudo unless absolutely necessary
   python main.py
   ```

2. **Use unprivileged port**:
   ```bash
   export FLASK_PORT=8080
   python main.py
   ```

3. **Check file permissions**:
   ```bash
   ls -la main.py
   chmod +x main.py  # If needed
   ```

### Problem: LibreAssistant Starts But UI Not Accessible

#### Browser Shows "Connection Refused"
**Cause**: Application isn't listening on the expected interface

**Solutions**:
1. **Check the startup logs** for the actual binding address
2. **Try different addresses**:
   - `http://localhost:5000`
   - `http://127.0.0.1:5000`
   - `http://0.0.0.0:5000`

3. **Configure host binding**:
   ```bash
   export FLASK_HOST=127.0.0.1
   python main.py
   ```

#### Browser Shows "This site can't be reached"
**Cause**: Network or firewall issues

**Solutions**:
1. **Check firewall settings**
2. **Try incognito/private browsing mode**
3. **Clear browser cache and cookies**
4. **Try a different browser**

## Ollama Connection Issues

### Problem: "Cannot Connect to Ollama Service"

#### Ollama Not Installed
**Solution**: Install Ollama from [ollama.ai](https://ollama.ai/)

**Verification**:
```bash
ollama --version
```

#### Ollama Not Running
**Symptoms**: Connection timeout, "service unavailable"

**Solutions**:
1. **Start Ollama service**:
   ```bash
   ollama serve
   ```

2. **Check if Ollama is running**:
   ```bash
   curl http://localhost:11434/api/tags
   ```

3. **Restart Ollama**:
   ```bash
   # Stop Ollama
   pkill ollama
   
   # Start Ollama
   ollama serve
   ```

#### Ollama Running on Different Port/Host
**Symptoms**: Connection refused, wrong endpoint

**Solutions**:
1. **Check Ollama configuration**:
   ```bash
   ollama show --help
   ```

2. **Update LibreAssistant configuration**:
   ```bash
   export OLLAMA_HOST=http://your-ollama-host:port
   python main.py
   ```

3. **Configure in Settings tab** (if UI is accessible)

#### Network/Firewall Blocking Connection
**Symptoms**: Timeouts, connection refused

**Solutions**:
1. **Check firewall rules**
2. **Verify network connectivity**:
   ```bash
   ping localhost
   telnet localhost 11434
   ```

3. **Try different network interfaces**

### Problem: "No Models Found"

#### No Models Downloaded
**Solution**: Download models using Ollama:
```bash
# Lightweight model for testing
ollama pull orca-mini:3b

# General purpose model
ollama pull llama2:7b

# List available models
ollama list
```

#### Models Not Accessible
**Solution**: Check Ollama model directory:
```bash
ollama list
```

If models appear in CLI but not in LibreAssistant:
1. Restart LibreAssistant
2. Check Ollama API response:
   ```bash
   curl http://localhost:11434/api/tags
   ```

## Plugin Issues

### Problem: Plugins Not Appearing

#### Plugin Discovery Failed
**Symptoms**: Empty plugin catalogue

**Solutions**:
1. **Check plugins directory exists**:
   ```bash
   ls -la plugins/
   ```

2. **Verify plugin manifests**:
   ```bash
   find plugins/ -name "plugin-manifest.json"
   ```

3. **Check manifest syntax**:
   ```bash
   python -m json.tool plugins/local_fileio/plugin-manifest.json
   ```

4. **Restart LibreAssistant**

#### Plugin Directory Permissions
**Symptoms**: "Permission denied" in logs

**Solutions**:
```bash
# Fix permissions
chmod -R 755 plugins/
chmod -R 644 plugins/*/plugin-manifest.json
```

### Problem: Plugin Won't Start

#### Missing Dependencies
**Symptoms**: "ModuleNotFoundError", import errors

**Solutions**:
1. **Check plugin requirements**:
   ```bash
   cat plugins/plugin_name/requirements.txt
   ```

2. **Install plugin dependencies**:
   ```bash
   cd plugins/plugin_name
   pip install -r requirements.txt
   ```

#### Port Conflicts
**Symptoms**: "Port already in use", binding errors

**Solutions**:
1. **Check used ports**:
   ```bash
   netstat -tulpn | grep :51[0-9][0-9]
   ```

2. **Modify plugin port** in `plugin-manifest.json`:
   ```json
   {
     "mcp_port": 5199
   }
   ```

3. **Stop conflicting services**

#### Configuration Errors
**Symptoms**: Plugin starts but doesn't work

**Solutions**:
1. **Verify plugin configuration**
2. **Check API keys and credentials**
3. **Review plugin logs** in Monitoring tab
4. **Test plugin independently**:
   ```bash
   cd plugins/plugin_name
   python server.py
   ```

### Problem: Plugin Permission Errors

#### File Access Denied
**Symptoms**: "Access denied", "Permission denied"

**Solutions**:
1. **Check configured base directory**:
   - Ensure directory exists
   - Verify write permissions
   - Check path is absolute

2. **Fix directory permissions**:
   ```bash
   chmod 755 /path/to/base/directory
   ```

3. **Update plugin configuration** with correct paths

#### API Key Issues
**Symptoms**: "Unauthorized", "Invalid credentials"

**Solutions**:
1. **Verify API key** is correct and active
2. **Check API key permissions** on the service
3. **Regenerate API key** if needed
4. **Update plugin configuration**

## Performance Issues

### Problem: Slow Responses

#### Large Model Size
**Symptoms**: Long response times, high memory usage

**Solutions**:
1. **Switch to smaller model**:
   ```bash
   ollama pull orca-mini:3b  # Faster, less memory
   ```

2. **Check available RAM**:
   ```bash
   free -h  # Linux
   vm_stat  # macOS
   ```

3. **Close other applications** to free memory

#### Too Many Active Plugins
**Symptoms**: Slow startup, high CPU usage

**Solutions**:
1. **Disable unused plugins** in Plugin Catalogue
2. **Monitor resource usage** in Monitoring tab
3. **Restart LibreAssistant** to free resources

#### System Resource Constraints
**Solutions**:
1. **Monitor system resources**:
   ```bash
   top         # Linux/macOS
   htop        # Better alternative
   ```

2. **Increase virtual memory** if needed
3. **Consider hardware upgrade** for better performance

### Problem: High Memory Usage

#### Model Memory Consumption
**Solutions**:
1. **Use quantized models** (smaller but slightly less accurate)
2. **Unload unused models** from Ollama
3. **Monitor with** `ollama ps`

#### Memory Leaks
**Symptoms**: Memory usage increases over time

**Solutions**:
1. **Restart LibreAssistant** periodically
2. **Monitor for memory leaks** in Monitoring tab
3. **Report the issue** if memory keeps growing

## Network and Connectivity Issues

### Problem: Plugin API Calls Failing

#### Network Connectivity
**Solutions**:
1. **Test internet connection**:
   ```bash
   ping google.com
   curl -I https://api.brave.com
   ```

2. **Check DNS resolution**:
   ```bash
   nslookup api.brave.com
   ```

3. **Test with different DNS servers**

#### Proxy/Firewall Issues
**Solutions**:
1. **Configure proxy settings** if needed
2. **Check corporate firewall rules**
3. **Try different network** (mobile hotspot, etc.)

#### Rate Limiting
**Symptoms**: "Too many requests", 429 errors

**Solutions**:
1. **Wait before retrying**
2. **Check API usage limits**
3. **Upgrade API plan** if needed

### Problem: Local Services Not Accessible

#### Localhost Resolution
**Solutions**:
1. **Check hosts file**:
   ```bash
   cat /etc/hosts  # Linux/macOS
   type C:\Windows\System32\drivers\etc\hosts  # Windows
   ```

2. **Ensure localhost points to 127.0.0.1**
3. **Try 127.0.0.1 instead of localhost**

## Data and Configuration Issues

### Problem: Configuration Not Persisting

#### File Permissions
**Solutions**:
1. **Check config file permissions**:
   ```bash
   ls -la *.json *.cfg
   ```

2. **Fix permissions**:
   ```bash
   chmod 644 plugin_config.json
   ```

#### Readonly Filesystem
**Solutions**:
1. **Check filesystem status**:
   ```bash
   mount | grep -w /
   ```

2. **Remount if readonly**:
   ```bash
   sudo mount -o remount,rw /
   ```

### Problem: Lost Chat History

#### Session Storage Issues
**Solutions**:
1. **Check browser storage** (currently in memory only)
2. **Clear browser cache** and restart
3. **Use different browser** to test

## Security and Permission Issues

### Problem: Security Warnings

#### File Access Restrictions
**Expected Behavior**: Plugins should only access configured directories

**If seeing unexpected access**:
1. **Review plugin permissions**
2. **Check sandbox configuration**
3. **Report security concern**

#### SSL/TLS Certificate Issues
**Solutions**:
1. **Update certificates**
2. **Check system time**
3. **Try different API endpoints**

## Development and Debug Mode Issues

### Problem: Debug Mode Not Working

#### Environment Configuration
**Solutions**:
```bash
export FLASK_DEBUG=true
export FLASK_ENV=development
python main.py
```

#### Logging Configuration
**Solutions**:
1. **Check log level**:
   ```bash
   export LOG_LEVEL=DEBUG
   ```

2. **Review log output** for errors
3. **Enable verbose logging** for plugins

## Getting Help

### Collecting Debug Information

#### System Information
```bash
# Operating system
uname -a

# Python version
python --version

# LibreAssistant version (from logs or about section)
grep -i version main.py

# Ollama version
ollama --version

# Available models
ollama list
```

#### Log Collection
1. **Application logs**: Check terminal output where you started LibreAssistant
2. **Browser console**: F12 → Console tab for JavaScript errors
3. **Network tab**: F12 → Network tab for API call failures
4. **Plugin logs**: Monitoring tab in LibreAssistant

#### Configuration Sanitization
Before sharing configuration:
1. **Remove API keys** and sensitive data
2. **Remove personal file paths**
3. **Keep structural information** intact

### Reporting Issues

#### GitHub Issues
When reporting on GitHub, include:
1. **Clear problem description**
2. **Steps to reproduce**
3. **Expected vs actual behavior**
4. **System information**
5. **Relevant log excerpts** (sanitized)
6. **Screenshots** if UI-related

#### Community Support
1. **Search existing issues** first
2. **Provide context** about your setup
3. **Be specific** about error messages
4. **Follow up** with additional info if requested

### Emergency Recovery

#### Complete Reset
If everything is broken:
```bash
# Stop all processes
pkill -f "python main.py"
pkill ollama

# Clean restart
ollama serve &
python main.py
```

#### Factory Reset
To start completely fresh:
1. **Backup important data**
2. **Stop all services**
3. **Remove configuration files** (after backup)
4. **Restart services**
5. **Reconfigure from scratch**

Remember: LibreAssistant is designed to be safe and recoverable. Most issues can be resolved without data loss, and the worst case scenario is reconfiguring your plugins and preferences.