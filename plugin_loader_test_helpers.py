import subprocess

def start_mcp_server(server_path):
    """Start an MCP server process for testing purposes."""
    proc = subprocess.Popen(['python', server_path])
    return proc

def stop_mcp_server(proc):
    """Stop an MCP server process for testing purposes."""
    proc.terminate()
    proc.wait(timeout=5)
