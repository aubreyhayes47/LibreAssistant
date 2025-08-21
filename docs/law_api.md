<!-- Copyright (c) 2024 LibreAssistant contributors. Licensed under the MIT License. -->

# Law Plugin

The `law_by_keystone` MCP server queries public government APIs to gather legal
and legislative information. Supported data sources include:

- **GovInfo** – federal publications
- **eCFR** – Electronic Code of Federal Regulations
- **CourtListener** – court opinions and dockets
- **Open States** – state legislative data
- **GovTrack** – congressional information

## Tool

`generate_legal_summary`

| Parameter       | Description                                                     |
| --------------- | --------------------------------------------------------------- |
| `query`         | Search term or citation                                         |
| `source`        | One of `govinfo`, `ecfr`, `courtlistener`, `openstates`, `govtrack` |
| `output_format` | `md`, `json`, `html`, `txt`, or `xml`                            |
| `output_path`   | Directory to write the result file                              |

The tool writes a file in the requested format and returns metadata including the
number of results and the data source used. Audit logs record the `dataSources`
array so requests can be traced back to their origins.

## Example

```json
{
  "plugin": "law_by_keystone",
  "user_id": "alice",
  "payload": {
    "query": "education",
    "source": "govinfo",
    "output_format": "md",
  "output_path": "law"
  }
}
```
