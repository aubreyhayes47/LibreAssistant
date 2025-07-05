use std::process::Command;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

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
}

// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[tauri::command]
async fn call_python_backend(command: String, payload: CommandPayload) -> Result<CommandResponse, String> {
    // Get the backend directory path (assuming it's relative to the executable)
    let backend_path = std::env::current_dir()
        .map_err(|e| format!("Failed to get current directory: {}", e))?
        .join("../../backend");
    
    // Serialize the payload to JSON
    let payload_json = serde_json::to_string(&payload)
        .map_err(|e| format!("Failed to serialize payload: {}", e))?;
    
    // Execute the Python command
    let output = Command::new("python")
        .arg("main.py")
        .arg(&command)
        .arg(&payload_json)
        .current_dir(&backend_path)
        .output()
        .map_err(|e| format!("Failed to execute Python command: {}", e))?;
    
    if !output.status.success() {
        let error_msg = String::from_utf8_lossy(&output.stderr);
        return Err(format!("Python command failed: {}", error_msg));
    }
    
    // Parse the JSON response
    let response_str = String::from_utf8_lossy(&output.stdout);
    let response: CommandResponse = serde_json::from_str(&response_str)
        .map_err(|e| format!("Failed to parse Python response: {}", e))?;
    
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

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            greet,
            hello_backend,
            process_url,
            get_browser_data,
            analyze_content
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
