# 💊 Reviewing System Health

LibreAssistant includes comprehensive system health monitoring to help you track performance, diagnose issues, and ensure optimal operation. The system health dashboard provides real-time insights into all system components.

## Overview

System Health monitoring includes:
- **Real-time Status**: Live monitoring of all system components
- **Performance Metrics**: Response times, uptime, and resource usage
- **Error Tracking**: Detailed error logs and diagnostics
- **Health Endpoints**: API access to system status information

## Step-by-Step Guide

### 1. Accessing System Health

There are multiple ways to access system health information:

**Option A: Main Navigation**
1. Click on the **System Health** tab in the main navigation
2. The health dashboard loads automatically
3. Real-time status information appears immediately

**Option B: System Integration Interface**
1. Navigate to the **System Integration and Data Flow** section
2. Find the System Health component
3. Use the integrated health monitoring tools

![System Health interface](https://github.com/user-attachments/assets/e74920d3-815d-4dc2-893d-d49c978e1dff)

### 2. Understanding Health Status Indicators

The system health dashboard uses clear visual indicators:

#### Overall System Status
- 🟢 **Healthy**: All systems operating normally
- 🟡 **Warning**: Some components have issues but system is functional
- 🔴 **Critical**: Major issues requiring immediate attention
- ⚪ **Unknown**: Unable to determine status (connection issues)

#### Component-Specific Status
- **API Endpoints**: Response times and availability
- **Database**: Connection status and performance
- **External Services**: Provider connections and plugin status
- **Resource Usage**: Memory, CPU, and storage metrics

### 3. Reading Health Information

The system health display provides detailed information:

1. **Current Status**
   - Overall system health summary
   - Individual component status
   - Last update timestamp

2. **Performance Metrics**
   - Response times for different operations
   - Uptime statistics
   - Resource utilization levels

3. **Error Information**
   - Recent errors and warnings
   - Error frequency and patterns
   - Suggested solutions

### 4. Refreshing Health Data

To get the latest system status:

1. **Automatic Refresh**
   - System health updates automatically every 30 seconds
   - Real-time updates appear without user intervention

2. **Manual Refresh**
   - Click the **Refresh** button to get immediate updates
   - Useful when investigating specific issues
   - Button shows loading state during refresh

3. **Auto-Refresh Configuration**
   - Enable/disable automatic refresh as needed
   - Adjust refresh interval in settings
   - Conserve resources when not actively monitoring

### 5. Handling Health Issues

When the system health shows problems:

#### Connection Errors
**Symptoms**: "Failed to load system health data: HTTP 404: File not found"
- **Immediate Action**: Check network connectivity
- **Verify**: Ensure LibreAssistant backend is running
- **Solution**: Restart the application or check server status

#### Performance Warnings
**Symptoms**: Slow response times or high resource usage
- **Investigate**: Review recent activity and usage patterns
- **Action**: Consider closing unnecessary applications
- **Monitor**: Watch for improvement over time

#### Component Failures
**Symptoms**: Specific components showing error status
- **Identify**: Note which components are affected
- **Isolate**: Test individual features to confirm issues
- **Resolve**: Follow component-specific troubleshooting steps

## Advanced Health Monitoring

### Health API Endpoints

LibreAssistant provides programmatic access to health data:

#### `/api/v1/health`
Returns comprehensive system health information:
```json
{
  "status": "healthy|warning|critical",
  "timestamp": "2024-01-01T12:00:00Z",
  "components": {
    "database": "healthy",
    "api": "healthy",
    "plugins": "warning"
  },
  "metrics": {
    "uptime": 86400,
    "memory_usage": 45.2,
    "response_time": 120
  }
}
```

#### `/api/v1/bom` (Bill of Materials)
Provides information about system components:
- **Dependencies**: Installed Python packages and versions
- **Models**: Available AI models and their locations
- **Datasets**: Accessible datasets and data sources

See the [Transparency Endpoints documentation](../transparency.md) for detailed API information.

### Monitoring Best Practices

1. **Regular Checks**
   - Review health status daily during active use
   - Set up monitoring alerts for critical issues
   - Track performance trends over time

2. **Proactive Monitoring**
   - Watch for performance degradation patterns
   - Monitor resource usage trends
   - Keep logs of recurring issues

3. **Documentation**
   - Record unusual events and their resolutions
   - Note system configuration changes
   - Maintain a troubleshooting log

### Performance Optimization

Based on health monitoring data:

#### Resource Management
- **Memory Usage**: Monitor memory consumption patterns
- **CPU Usage**: Track processing load during different operations
- **Storage**: Watch disk space usage for logs and data

#### Network Performance
- **Connection Quality**: Monitor AI provider response times
- **Bandwidth Usage**: Track data transfer for cloud providers
- **Latency**: Measure round-trip times for requests

#### Application Performance
- **Response Times**: Track request processing speed
- **Error Rates**: Monitor failure frequencies
- **Throughput**: Measure requests handled per time period

## Troubleshooting with Health Data

### Diagnostic Process

1. **Gather Information**
   - Check overall system status
   - Review component-specific errors
   - Note timing of issues

2. **Analyze Patterns**
   - Look for recurring problems
   - Identify correlation with specific actions
   - Check if issues are time-related

3. **Test Components**
   - Isolate problematic components
   - Test individual features separately
   - Verify fixes with health monitoring

### Common Health Issues

#### Backend Connection Problems
**Symptoms**: HTTP 404 or 500 errors in health data
- **Check**: Verify backend service is running
- **Solution**: Restart LibreAssistant services
- **Prevention**: Set up service monitoring

#### Provider Connection Issues
**Symptoms**: AI provider errors or timeouts
- **Check**: Test provider connectivity separately
- **Solution**: Switch to backup provider temporarily
- **Monitor**: Track provider reliability over time

#### Plugin Failures
**Symptoms**: Plugin-specific errors or warnings
- **Diagnose**: Check individual plugin status
- **Solution**: Disable problematic plugins temporarily
- **Fix**: Update or reconfigure affected plugins

#### Resource Exhaustion
**Symptoms**: High memory/CPU usage warnings
- **Immediate**: Close unnecessary applications
- **Long-term**: Consider hardware upgrades
- **Monitor**: Track usage patterns for optimization

## Integration with Other Features

### Plugin Health Monitoring

The health system monitors plugin performance:
- **Plugin Status**: Individual plugin health and errors
- **Resource Usage**: Plugin-specific resource consumption
- **Error Tracking**: Plugin-related error logging

### Provider Health Tracking

AI provider connections are monitored:
- **Response Times**: Track provider performance
- **Success Rates**: Monitor request success/failure ratios
- **Availability**: Track provider uptime and connectivity

### Theme System Health

Even theme operations are monitored:
- **Theme Loading**: Track theme installation and switching
- **Resource Impact**: Monitor theme performance impact
- **Error Detection**: Catch theme-related issues

## Health Monitoring Interface Features

The system health interface provides:

![Health monitoring feedback](https://github.com/user-attachments/assets/ac6a4413-9faa-42f1-8183-bbab2df2336b)

### Real-time Updates
- **Live Status**: Continuous monitoring and updates
- **Timestamp Tracking**: Clear indication of last update time
- **Automatic Refresh**: Configurable auto-refresh intervals

### User Feedback
- **Loading Indicators**: Clear feedback during health checks
- **Error Messages**: Detailed error information with timestamps
- **Status History**: Track status changes over time

### Interactive Controls
- **Manual Refresh**: On-demand health data updates
- **Component Details**: Drill down into specific component health
- **Export Options**: Save health reports for analysis

## Accessibility in Health Monitoring

The health monitoring system is designed for accessibility:
- **Screen Reader Support**: All status information is screen reader accessible
- **High Contrast**: Health indicators work with high contrast themes
- **Keyboard Navigation**: Full keyboard access to all health features
- **Clear Language**: Plain language descriptions of technical issues

## Security Considerations

Health monitoring respects security and privacy:
- **No Sensitive Data**: Health endpoints don't expose sensitive information
- **Authentication**: Health data access follows system authentication
- **Audit Trails**: Health access is logged for security
- **Data Minimization**: Only necessary health data is collected

---

**Congratulations!** You now have comprehensive knowledge of all four key LibreAssistant features. For additional help, check the [main documentation](../../README.md) or explore the [API documentation](../api.md) for technical details.