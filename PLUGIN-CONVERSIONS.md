# Plugin Conversion Notes

## Echo Plugin → MCP
- Tool `echo_message`
- Params: `{ message: string }`
- Returns: `{ echo: string }`
- Resource: `echo:last_message`
- Prompt: `echo_template`

## File I/O Plugin → MCP
- Tools: `fs_read`, `fs_create`, `fs_update` (confirm required), `fs_delete` (confirm required), `fs_list`
- Params/Returns follow JSON Schemas in server implementation
- Resources: `file://` and `dir://` style URIs managed by the server
- Prompt: `file_edit_template`

## Law by Keystone → MCP
- Tool `generate_legal_summary`
- Params: `{ query: string, output_format: md|txt|json, output_path?: string }`
- Returns: `{ summary: string, export_path?: string }`
- Resource: `law:last_summary`
- Prompt: `legal_research_template`

## ThinkTank → MCP
- Tool `analyze_goal`
- Params: `{ goal: string }`
- Returns structured dossier with `summary` and `analysis` fields
- Resource: `thinktank:last_dossier`
- Prompt: `thinktank_question_template`
