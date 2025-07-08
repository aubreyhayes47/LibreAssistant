use std::process::Command;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use uuid::Uuid;

#[derive(Serialize, Deserialize)]
struct CommandPayload {
    #[serde(flatten)]
    data: HashMap<String, serde_json::Value>,
}

#[derive(Serialize, Deserialize)]
struct CommandResponse {
    success: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    message: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    response: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    timestamp: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    url: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    title: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    content: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    r#type: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    data: Option<serde_json::Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    count: Option<i32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    analysis: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    keywords: Option<Vec<String>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    summary: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    session_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    role: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    messages: Option<Vec<serde_json::Value>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    model: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    context_summary: Option<serde_json::Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    history: Option<Vec<serde_json::Value>>,
}

// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[tauri::command]
async fn call_python_backend(command: String, payload: CommandPayload) -> Result<CommandResponse, String> {
    // Get the backend directory path
    let current_dir = std::env::current_dir()
        .map_err(|e| format!("Failed to get current directory: {}", e))?;
    
    let backend_path = if cfg!(debug_assertions) {
        // In development mode, we're likely in frontend/src-tauri/target/debug
        // Navigate to the workspace root and then to backend
        let mut path = current_dir.clone();
        
        // Keep going up until we find the workspace root (contains both frontend and backend)
        while !path.join("backend").exists() && !path.join("frontend").exists() {
            if let Some(parent) = path.parent() {
                path = parent.to_path_buf();
            } else {
                return Err("Could not find workspace root directory".to_string());
            }
        }
        
        // If we're in frontend or src-tauri, go up to workspace root
        if path.file_name() == Some(std::ffi::OsStr::new("frontend")) || 
           path.file_name() == Some(std::ffi::OsStr::new("src-tauri")) ||
           path.file_name() == Some(std::ffi::OsStr::new("debug")) {
            while path.file_name() != Some(std::ffi::OsStr::new("browser")) {
                if let Some(parent) = path.parent() {
                    path = parent.to_path_buf();
                } else {
                    break;
                }
            }
        }
        
        path.join("backend")
    } else {
        // In production, assume backend is relative to the executable
        current_dir.join("backend")
    };
    
    // Validate that the backend directory exists
    if !backend_path.exists() {
        return Err(format!("Backend directory does not exist: {:?}", backend_path));
    }
    
    // Serialize the payload to JSON
    let payload_json = serde_json::to_string(&payload)
        .map_err(|e| format!("Failed to serialize payload: {}", e))?;
    
    // Debug logging
    eprintln!("Current dir: {:?}", current_dir);
    eprintln!("Backend path: {:?}", backend_path);
    eprintln!("Command: {}", command);
    eprintln!("Payload: {}", payload_json);
    
    // Execute the Python command
    let python_executable = if cfg!(target_os = "windows") {
        // On Windows, check for virtual environment first
        let venv_python = backend_path.join("venv").join("Scripts").join("python.exe");
        if venv_python.exists() {
            venv_python.to_string_lossy().to_string()
        } else {
            "python.exe".to_string()
        }
    } else {
        // On Unix-like systems
        let venv_python = backend_path.join("venv").join("bin").join("python");
        if venv_python.exists() {
            venv_python.to_string_lossy().to_string()
        } else {
            "python".to_string()
        }
    };
    
    eprintln!("Using Python executable: {}", python_executable);
    
    // Create a temporary file for the JSON payload to avoid shell escaping issues
    let temp_file = backend_path.join("temp_payload.json");
    std::fs::write(&temp_file, &payload_json)
        .map_err(|e| format!("Failed to write temp file: {}", e))?;
    
    let output = Command::new(&python_executable)
        .arg("main.py")
        .arg(&command)
        .arg(&temp_file.to_string_lossy().to_string())
        .current_dir(&backend_path)
        .env("PYTHONIOENCODING", "utf-8")
        .env("PYTHONPATH", backend_path.to_string_lossy().to_string())
        .output()
        .map_err(|e| format!("Failed to execute Python command: {}", e))?;
    
    // Clean up temp file
    let _ = std::fs::remove_file(&temp_file);
    
    if !output.status.success() {
        let error_msg = String::from_utf8_lossy(&output.stderr);
        let stdout_msg = String::from_utf8_lossy(&output.stdout);
        return Err(format!("Python command failed: stderr: {}, stdout: {}", error_msg, stdout_msg));
    }
    
    // Parse the JSON response
    let response_str = String::from_utf8_lossy(&output.stdout);
    
    // Debug logging
    eprintln!("Python response: {}", response_str);
    
    let response: CommandResponse = serde_json::from_str(&response_str)
        .map_err(|e| format!("Failed to parse Python response: {} (response was: {})", e, response_str))?;
    
    Ok(response)
}

#[tauri::command]
async fn hello_backend(name: String) -> Result<CommandResponse, String> {
    let mut payload_data = HashMap::new();
    payload_data.insert("name".to_string(), serde_json::Value::String(name));
    payload_data.insert("timestamp".to_string(), serde_json::Value::String(
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_secs()
            .to_string()
    ));
    
    call_python_backend("hello".to_string(), CommandPayload { data: payload_data }).await
}

#[tauri::command]
async fn process_url(url: String) -> Result<CommandResponse, String> {
    let mut payload_data = HashMap::new();
    payload_data.insert("url".to_string(), serde_json::Value::String(url));

    call_python_backend("process_url".to_string(), CommandPayload { data: payload_data }).await
}

#[tauri::command]
async fn summarize_page(url: String) -> Result<CommandResponse, String> {
    let mut payload_data = HashMap::new();
    payload_data.insert("url".to_string(), serde_json::Value::String(url));

    call_python_backend("summarize_page".to_string(), CommandPayload { data: payload_data }).await
}

#[tauri::command]
async fn get_browser_data(data_type: String) -> Result<CommandResponse, String> {
    let mut payload_data = HashMap::new();
    payload_data.insert("type".to_string(), serde_json::Value::String(data_type));
    
    call_python_backend("get_browser_data".to_string(), CommandPayload { data: payload_data }).await
}

#[tauri::command]
async fn analyze_content(content: String) -> Result<CommandResponse, String> {
    let mut payload_data = HashMap::new();
    payload_data.insert("content".to_string(), serde_json::Value::String(content));
    
    call_python_backend("analyze_content".to_string(), CommandPayload { data: payload_data }).await
}

// Phase 1B: New Tauri commands for chat and database operations

#[tauri::command]
async fn init_database() -> Result<CommandResponse, String> {
    let payload_data = HashMap::new();
    call_python_backend("init_database".to_string(), CommandPayload { data: payload_data }).await
}

#[tauri::command]
async fn chat_with_llm(message: String, session_id: Option<String>) -> Result<CommandResponse, String> {
    let mut payload_data = HashMap::new();
    payload_data.insert("message".to_string(), serde_json::Value::String(message));
    
    // Generate or use provided session ID
    let session = session_id.unwrap_or_else(|| Uuid::new_v4().to_string());
    payload_data.insert("session_id".to_string(), serde_json::Value::String(session));
    
    call_python_backend("chat_with_llm".to_string(), CommandPayload { data: payload_data }).await
}

#[tauri::command]
async fn save_bookmark(url: String, title: String, content: Option<String>) -> Result<CommandResponse, String> {
    let mut payload_data = HashMap::new();
    payload_data.insert("url".to_string(), serde_json::Value::String(url));
    payload_data.insert("title".to_string(), serde_json::Value::String(title));
    
    if let Some(content_text) = content {
        payload_data.insert("content".to_string(), serde_json::Value::String(content_text));
    }
    
    call_python_backend("save_bookmark".to_string(), CommandPayload { data: payload_data }).await
}

#[tauri::command]
async fn get_chat_history(session_id: Option<String>, limit: Option<i32>) -> Result<CommandResponse, String> {
    let mut payload_data = HashMap::new();
    
    if let Some(session) = session_id {
        payload_data.insert("session_id".to_string(), serde_json::Value::String(session));
    }
    
    if let Some(msg_limit) = limit {
        payload_data.insert("limit".to_string(), serde_json::Value::Number(serde_json::Number::from(msg_limit)));
    }
    
    call_python_backend("get_chat_history".to_string(), CommandPayload { data: payload_data }).await
}

#[tauri::command]
async fn get_bookmarks(search_query: Option<String>) -> Result<CommandResponse, String> {
    let mut payload_data = HashMap::new();
    
    if let Some(query) = search_query {
        payload_data.insert("search_query".to_string(), serde_json::Value::String(query));
    }
    
    call_python_backend("get_bookmarks".to_string(), CommandPayload { data: payload_data }).await
}

#[tauri::command]
async fn search_bookmarks(query: String, limit: Option<i32>) -> Result<CommandResponse, String> {
    let mut payload_data = HashMap::new();
    payload_data.insert("query".to_string(), serde_json::Value::String(query));
    
    if let Some(search_limit) = limit {
        payload_data.insert("limit".to_string(), serde_json::Value::Number(serde_json::Number::from(search_limit)));
    }
    
    call_python_backend("search_bookmarks".to_string(), CommandPayload { data: payload_data }).await
}

#[tauri::command]
async fn get_browser_history(limit: Option<i32>, search_query: Option<String>) -> Result<CommandResponse, String> {
    let mut payload_data = HashMap::new();
    
    if let Some(history_limit) = limit {
        payload_data.insert("limit".to_string(), serde_json::Value::Number(serde_json::Number::from(history_limit)));
    }
    
    if let Some(query) = search_query {
        payload_data.insert("search_query".to_string(), serde_json::Value::String(query));
    }
    
    call_python_backend("get_browser_history".to_string(), CommandPayload { data: payload_data }).await
}

#[tauri::command]
async fn add_history_entry(url: String, title: String, visit_time: Option<String>) -> Result<CommandResponse, String> {
    let mut payload_data = HashMap::new();
    payload_data.insert("url".to_string(), serde_json::Value::String(url));
    payload_data.insert("title".to_string(), serde_json::Value::String(title));
    
    // Use provided visit_time or current timestamp
    let timestamp = visit_time.unwrap_or_else(|| {
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_secs()
            .to_string()
    });
    payload_data.insert("visit_time".to_string(), serde_json::Value::String(timestamp));
    
    call_python_backend("add_history_entry".to_string(), CommandPayload { data: payload_data }).await
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            greet,
            hello_backend,
            process_url,
            get_browser_data,
            analyze_content,
            init_database,
            chat_with_llm,
            save_bookmark,
            get_chat_history,
            get_bookmarks,
            search_bookmarks,
            get_browser_history,
            add_history_entry,
            summarize_page
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
