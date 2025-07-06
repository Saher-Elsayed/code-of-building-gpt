\# MCP Integration for Building Code GPT + Revit



This document explains how to set up and use the Model Context Protocol (MCP) integration that connects your Building Code GPT system with Autodesk Revit for automated building code compliance.



\## What This Integration Provides



\### Core Capabilities

\- \*\*Intelligent Code Queries\*\*: Ask natural language questions about building codes and get precise, cited answers

\- \*\*Automated Revit Scripts\*\*: Generate Python scripts for Revit based on building code requirements

\- \*\*Height Restrictions\*\*: Automatically apply zoning height limits to your Revit model

\- \*\*Setback Compliance\*\*: Check and enforce setback requirements

\- \*\*Compliance Reports\*\*: Generate comprehensive building code compliance reports

\- \*\*Real-time Automation\*\*: Execute building code compliance checks directly from chat prompts



\### Example Use Cases

```

"Apply 35-foot height limit for R1 zoning to all walls and columns"

→ Generates and can execute Revit script to modify building elements



"Check setback compliance with 20ft front, 10ft side, 15ft rear"

→ Analyzes model geometry and reports violations



"Generate compliance report for residential building in California"

→ Queries relevant codes and creates detailed report



"What are the fire safety requirements for commercial buildings?"

→ Searches code database and provides cited answers

```



\## Quick Setup



\### 1. Run the Setup Script

```bash

\# Windows

setup\_mcp\_integration.bat



\# This will:

\# - Install MCP dependencies

\# - Create necessary directories

\# - Set up configuration files

\# - Create helper scripts

```



\### 2. Verify Installation

```bash

\# Test MCP integration

test\_mcp.bat



\# Should output: "MCP integration initialized successfully"

```



\### 3. Start the Enhanced Application

```bash

\# Start Ollama (in separate terminal)

ollama serve



\# Run enhanced app with MCP support

run\_enhanced\_app.bat

```



\## 📋 Prerequisites



\### Required Software

\- \*\*Python 3.8+\*\* with pip

\- \*\*Ollama\*\* (for local LLM)

\- \*\*Tesseract OCR\*\* (for document processing)

\- \*\*Poppler\*\* (for PDF processing)

\- \*\*Autodesk Revit\*\* (for script execution)



\### Python Dependencies

The setup script installs these automatically:

```

\# Core MCP

mcp>=1.0.0

asyncio-mqtt>=0.13.0

jsonschema>=4.0.0



\# Existing project dependencies

streamlit>=1.28.0

sentence-transformers>=2.2.2

chromadb>=0.4.0

pytesseract>=0.3.10

\# ... (see requirements.txt)

```



\## 🏗️ Architecture Overview



```

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐

│   Streamlit UI  │◄──►│   MCP Server    │◄──►│  Revit Model    │

│                 │    │                 │    │                 │

│ • Chat Interface│    │ • Code Queries  │    │ • Element Mod.  │

│ • File Upload   │    │ • Script Gen.   │    │ • Parameter Set │

│ • Automation UI │    │ • Compliance    │    │ • Validation    │

└─────────────────┘    └─────────────────┘    └─────────────────┘

&nbsp;        ▲                       ▲                       ▲

&nbsp;        │                       │                       │

&nbsp;        ▼                       ▼                       ▼

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐

│  Vector Store   │    │   Local LLM     │    │   File System   │

│                 │    │                 │    │                 │

│ • Code Chunks   │    │ • Llama2:7b     │    │ • Generated     │

│ • Embeddings    │    │ • Response Gen. │    │   Scripts       │

│ • Retrieval     │    │ • Code Analysis │    │ • Reports       │

└─────────────────┘    └─────────────────┘    └─────────────────┘

```



\## 🛠️ MCP Tools Available



\### 1. `query\_building\_codes`

\*\*Purpose\*\*: Search building codes in your vector database

\*\*Parameters\*\*:

\- `query` (string): Natural language query

\- `k` (integer): Number of results to return



\*\*Example\*\*:

```json

{

&nbsp; "name": "query\_building\_codes",

&nbsp; "arguments": {

&nbsp;   "query": "residential building height limits California",

&nbsp;   "k": 5

&nbsp; }

}

```



\### 2. `apply\_height\_restrictions`

\*\*Purpose\*\*: Generate script to apply height limits in Revit

\*\*Parameters\*\*:

\- `zone\_type` (string): Zoning classification (R1, R2, C1, etc.)

\- `max\_height` (number): Maximum height in feet

\- `element\_categories` (array): Revit elements to modify



\*\*Example\*\*:

```json

{

&nbsp; "name": "apply\_height\_restrictions",

&nbsp; "arguments": {

&nbsp;   "zone\_type": "R1",

&nbsp;   "max\_height": 35,

&nbsp;   "element\_categories": \["Walls", "Columns"]

&nbsp; }

}

```



\### 3. `check\_setback\_compliance`

\*\*Purpose\*\*: Generate script to check building setbacks

\*\*Parameters\*\*:

\- `front\_setback` (number): Front setback in feet

\- `side\_setback` (number): Side setback in feet  

\- `rear\_setback` (number): Rear setback in feet

\- `property\_lines` (array): Property boundary coordinates



\### 4. `create\_code\_compliance\_report`

\*\*Purpose\*\*: Generate comprehensive compliance report

\*\*Parameters\*\*:

\- `project\_name` (string): Name of the project

\- `building\_type` (string): Type of building

\- `check\_categories` (array): Categories to check



\### 5. `generate\_revit\_script`

\*\*Purpose\*\*: Generate custom Revit script from code requirements

\*\*Parameters\*\*:

\- `code\_requirement` (string): Natural language requirement

\- `script\_type` (string): "python", "dynamo", or "c#"



\## 💬 Natural Language Commands



The system recognizes these types of natural language inputs:



\### Height Restrictions

```

"Apply 35-foot height limit for R1 zoning"

"Set maximum building height to 50 feet for commercial zone"

"Limit wall heights to 30 feet"

```



\### Setback Compliance

```

"Check setbacks with 20 front, 10 side, 15 rear"

"Verify 25-foot front setback compliance"

"Apply uniform 15-foot setbacks"

```



\### Script Generation

```

"Generate script to modify all windows for energy compliance"

"Create Revit automation for fire safety requirements"

"Script to check ADA accessibility compliance"

```



\### Code Queries

```

"What are the fire safety requirements for high-rise buildings?"

"Find parking requirements for commercial buildings"

"Show me accessibility standards for public buildings"

```



\## 📁 File Organization



After setup, your project structure will include:



```

code\_of\_building\_gpt/

├── mcp/

│   ├── \_\_init\_\_.py

│   ├── mcp\_server.py           # Main MCP server

│   └── mcp\_integration.py      # Integration utilities

├── revit\_scripts/

│   ├── template.py             # Script template

│   └── \*.py                    # Generated scripts

├── generated\_scripts/          # Custom user scripts

├── compliance\_reports/         # Generated reports

├── mcp\_config.json            # MCP configuration

├── run\_enhanced\_app.bat       # Enhanced startup script

├── test\_mcp.bat              # MCP test script

└── setup\_mcp\_integration.bat  # Setup script

```



\## 🔧 Usage Examples



\### Example 1: Height Restriction Workflow

1\. \*\*Upload building codes\*\* via Streamlit sidebar

2\. \*\*Connect MCP\*\* using sidebar button

3\. \*\*Chat command\*\*: "Apply 35-foot height limit for R1 zoning to all building elements"

4\. \*\*Result\*\*: Script generated and displayed, ready for Revit execution



\### Example 2: Compliance Report Generation

1\. Navigate to \*\*"Compliance Reports"\*\* tab

2\. Fill in project details:

&nbsp;  - Project Name: "Downtown Residential"

&nbsp;  - Building Type: "residential"

&nbsp;  - Categories: height, setbacks, fire\_safety

3\. Click \*\*"Generate Compliance Report"\*\*

4\. \*\*Result\*\*: Comprehensive report with code citations



\### Example 3: Custom Script Generation

1\. Navigate to \*\*"Revit Automation"\*\* tab

2\. In \*\*"Custom Script"\*\* section:

&nbsp;  - Requirement: "Ensure all doors meet ADA width requirements"

&nbsp;  - Script Type: "python"

3\. Click \*\*"Generate Script"\*\*

4\. \*\*Result\*\*: Revit Python script for ADA compliance



\## 🚨 Troubleshooting



\### Common Issues



\#### MCP Connection Failed

```

Error: MCP Connection Failed

```

\*\*Solutions\*\*:

1\. Ensure Python environment is activated

2\. Check that all MCP dependencies are installed

3\. Verify `.env` file configuration

4\. Run `test\_mcp.bat` to diagnose



\#### Ollama Not Running

```

Error: Ollama is not running

```

\*\*Solutions\*\*:

1\. Start Ollama: `ollama serve`

2\. Verify model is pulled: `ollama pull llama2:7b`

3\. Check Ollama URL in `.env`: `OLLAMA\_BASE\_URL=http://127.0.0.1:11434`



\#### No Building Codes Found

```

No relevant sections found

```

\*\*Solutions\*\*:

1\. Upload PDF building codes via sidebar

2\. Wait for processing to complete

3\. Verify vector database path in `.env`

4\. Check OCR processing succeeded



\#### Script Generation Errors

```

Error generating Revit script

```

\*\*Solutions\*\*:

1\. Ensure MCP server is connected

2\. Check LLM is responding (test with simple query)

3\. Verify building codes are loaded

4\. Try simpler/clearer requirements



\### Debug Mode

Enable debug information in the sidebar:

1\. Check \*\*"Show Debug Info"\*\* in sidebar

2\. Review connection status

3\. Check session state

4\. Verify component initialization



\## 🔮 Advanced Usage



\### Custom MCP Tools

You can extend the MCP server with custom tools by:



1\. \*\*Adding new tool definitions\*\* in `mcp\_server.py`

2\. \*\*Implementing tool handlers\*\* in the `handle\_call\_tool` function

3\. \*\*Testing tools\*\* via the enhanced Streamlit interface



\### Integration with Other Software

The MCP architecture allows integration with:

\- \*\*AutoCAD\*\* (via AutoCAD API)

\- \*\*SketchUp\*\* (via Ruby API)

\- \*\*Dynamo\*\* (via Dynamo scripting)

\- \*\*Grasshopper\*\* (via Python scripting)



\### Custom Code Databases

To add specialized building codes:



1\. \*\*Upload PDFs\*\* via Streamlit interface

2\. \*\*Verify OCR processing\*\* in debug mode

3\. \*\*Test retrieval\*\* with sample queries

4\. \*\*Adjust chunk size/overlap\*\* in `.env` if needed



\## Support



For issues and questions:



1\. \*\*Check Debug Info\*\* in Streamlit sidebar

2\. \*\*Review logs\*\* in console output

3\. \*\*Test components\*\* individually using test scripts

4\. \*\*Verify prerequisites\*\* are properly installed



\## 🚀 Next Steps



Consider these enhancements:

\- \*\*Cloud deployment\*\* for team access

\- \*\*Additional CAD integrations\*\*

\- \*\*Custom building code parsers\*\*

\- \*\*Advanced compliance analytics\*\*

\- \*\*Integration with BIM 360/ACC\*\*



---



\*This MCP integration transforms your Building Code GPT into a powerful automation platform that bridges AI-powered code analysis with practical BIM workflows.\*

