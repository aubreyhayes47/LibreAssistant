#!/usr/bin/env python3
"""
Enhanced Plugin Usage Tracking for LibreAssistant

This module provides a thread-safe, request-scoped plugin usage tracking system
that addresses the inconsistencies and race conditions in the current implementation.
"""

import time
import threading
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class PluginInvocation:
    """Represents a single plugin invocation with detailed metadata"""
    plugin_id: str
    input_parameters: Dict[str, Any]
    reason: str
    timestamp: float
    invocation_index: int  # Order within the request session
    success: Optional[bool] = None  # Will be set after plugin execution
    result: Optional[Dict[str, Any]] = None  # Plugin execution result
    error: Optional[str] = None  # Error message if execution failed
    execution_time_ms: Optional[float] = None  # Time taken to execute


class PluginUsageTracker:
    """
    Thread-safe plugin usage tracker that maintains request-scoped tracking
    with detailed invocation information and proper session isolation.
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        self._request_sessions: Dict[str, List[PluginInvocation]] = {}
        self._active_request_id: Optional[str] = None
        self._recent_sessions: List[Dict[str, Any]] = []
        self._max_recent_sessions = 20
    
    def start_request_session(self, request_id: str) -> None:
        """Start a new request session for plugin tracking"""
        with self._lock:
            # Only create new session if it doesn't already exist
            if request_id not in self._request_sessions:
                self._request_sessions[request_id] = []
            
            # Update active request ID for convenience methods
            self._active_request_id = request_id
    
    def record_plugin_invocation(
        self,
        request_id: str,
        plugin_id: str,
        input_parameters: Dict[str, Any],
        reason: str
    ) -> PluginInvocation:
        """Record a plugin invocation for the specified request"""
        with self._lock:
            if request_id not in self._request_sessions:
                self._request_sessions[request_id] = []
            
            session = self._request_sessions[request_id]
            invocation = PluginInvocation(
                plugin_id=plugin_id,
                input_parameters=input_parameters.copy(),
                reason=reason,
                timestamp=time.time(),
                invocation_index=len(session)
            )
            
            session.append(invocation)
            return invocation
    
    def update_invocation_result(
        self,
        request_id: str,
        invocation_index: int,
        success: bool,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        execution_time_ms: Optional[float] = None
    ) -> None:
        """Update the result of a plugin invocation"""
        with self._lock:
            if request_id in self._request_sessions:
                session = self._request_sessions[request_id]
                if 0 <= invocation_index < len(session):
                    invocation = session[invocation_index]
                    invocation.success = success
                    invocation.result = result.copy() if result else None
                    invocation.error = error
                    invocation.execution_time_ms = execution_time_ms
    
    def get_request_session(self, request_id: str) -> List[PluginInvocation]:
        """Get all plugin invocations for a specific request"""
        with self._lock:
            # Check active sessions first
            if request_id in self._request_sessions:
                return self._request_sessions[request_id].copy()
            
            # Check archived sessions
            for archived in self._recent_sessions:
                if archived['request_id'] == request_id and 'invocations' in archived:
                    return archived['invocations'].copy()
            
            return []
    
    def get_active_session(self) -> Optional[List[PluginInvocation]]:
        """Get the current active request session"""
        with self._lock:
            if self._active_request_id:
                return self.get_request_session(self._active_request_id)
            return None
    
    def get_active_request_id(self) -> Optional[str]:
        """Get the current active request ID"""
        with self._lock:
            return self._active_request_id
    
    def get_session_summary(self, request_id: str) -> Dict[str, Any]:
        """Get a summary of plugin usage for a request session"""
        with self._lock:
            session = self._request_sessions.get(request_id, [])
            
            # Count invocations per plugin
            plugin_counts = defaultdict(int)
            plugin_details = defaultdict(list)
            
            for invocation in session:
                plugin_counts[invocation.plugin_id] += 1
                plugin_details[invocation.plugin_id].append({
                    'timestamp': invocation.timestamp,
                    'reason': invocation.reason,
                    'success': invocation.success,
                    'invocation_index': invocation.invocation_index
                })
            
            return {
                'request_id': request_id,
                'total_invocations': len(session),
                'unique_plugins': len(plugin_counts),
                'plugin_counts': dict(plugin_counts),
                'plugin_details': dict(plugin_details),
                'session_start_time': session[0].timestamp if session else None,
                'session_end_time': session[-1].timestamp if session else None
            }
    
    def get_plugins_used_list(self, request_id: str) -> List[Dict[str, Any]]:
        """Get a list of plugins used in the format expected by the API"""
        with self._lock:
            session = self._request_sessions.get(request_id, [])
            return [
                {
                    'id': invocation.plugin_id,
                    'reason': invocation.reason,
                    'input': invocation.input_parameters,
                    'timestamp': invocation.timestamp,
                    'invocation_index': invocation.invocation_index,
                    'success': invocation.success
                }
                for invocation in session
            ]
    
    def check_consecutive_duplicate(
        self,
        request_id: str,
        plugin_id: str,
        input_parameters: Dict[str, Any]
    ) -> bool:
        """Check if this would be a consecutive duplicate plugin call"""
        with self._lock:
            session = self._request_sessions.get(request_id, [])
            if not session:
                return False
            
            last_invocation = session[-1]
            return (
                last_invocation.plugin_id == plugin_id and
                last_invocation.input_parameters == input_parameters
            )
    
    def _archive_session(self, request_id: str) -> None:
        """Archive a completed request session"""
        if request_id in self._request_sessions:
            session = self._request_sessions[request_id]
            if session:
                self._recent_sessions.append({
                    'request_id': request_id,
                    'timestamp': session[0].timestamp,
                    'plugins': [inv.plugin_id for inv in session],
                    'total_invocations': len(session),
                    'invocations': session.copy(),  # Keep full invocation data
                    'summary': self.get_session_summary(request_id)
                })
                
                # Keep only recent sessions
                if len(self._recent_sessions) > self._max_recent_sessions:
                    self._recent_sessions.pop(0)
            
            # Clean up the session data
            del self._request_sessions[request_id]
    
    def get_recent_sessions(self) -> List[Dict[str, Any]]:
        """Get a list of recent request sessions"""
        with self._lock:
            return self._recent_sessions.copy()
    
    def cleanup_old_sessions(self, max_age_seconds: float = 3600) -> None:
        """Clean up old request sessions to prevent memory leaks"""
        current_time = time.time()
        with self._lock:
            # Clean up old active sessions
            to_remove = []
            for request_id, session in self._request_sessions.items():
                if session and (current_time - session[0].timestamp) > max_age_seconds:
                    to_remove.append(request_id)
            
            for request_id in to_remove:
                self._archive_session(request_id)
            
            # Clean up old recent sessions
            self._recent_sessions = [
                s for s in self._recent_sessions
                if (current_time - s['timestamp']) <= max_age_seconds
            ]


# Global tracker instance
plugin_tracker = PluginUsageTracker()