"""
MCP Integration Module for Building Code GPT + Revit
Handles communication with MCP server and Revit automation
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import subprocess
import os

logger = logging.getLogger(__name__)

class MCPRevitIntegration:
    def __init__(self, server_path: str = "mcp/mcp_server.py"):
        self.server_path = server_path
        self.server_process = None
        self.is_connected = False
        
    async def start_server(self):
        """Start the MCP server"""
        try:
            self.server_process = await asyncio.create_subprocess_exec(
                'python', self.server_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            self.is_connected = True
            logger.info("MCP server started successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            return False
    
    async def stop_server(self):
        """Stop the MCP server"""
        if self.server_process:
            self.server_process.terminate()
            await self.server_process.wait()
            self.is_connected = False
            logger.info("MCP server stopped")
    
    async def send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to the MCP server"""
        if not self.is_connected:
            await self.start_server()
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }
        
        try:
            # Send request via stdio
            request_json = json.dumps(request) + "\n"
            self.server_process.stdin.write(request_json.encode())
            await self.server_process.stdin.drain()
            
            # Read response
            response_line = await self.server_process.stdout.readline()
            response = json.loads(response_line.decode())
            
            return response
        except Exception as e:
            logger.error(f"Failed to send MCP request: {e}")
            return {"error": str(e)}
    
    async def query_building_codes(self, query: str, k: int = 5) -> Dict[str, Any]:
        """Query building codes via MCP"""
        return await self.send_request("tools/call", {
            "name": "query_building_codes",
            "arguments": {
                "query": query,
                "k": k
            }
        })
    
    async def apply_height_restrictions(self, zone_type: str, max_height: float, 
                                      element_categories: List[str] = None) -> Dict[str, Any]:
        """Apply height restrictions to Revit model"""
        if element_categories is None:
            element_categories = ["Walls", "Columns", "Structural Framing"]
        
        return await self.send_request("tools/call", {
            "name": "apply_height_restrictions",
            "arguments": {
                "zone_type": zone_type,
                "max_height": max_height,
                "element_categories": element_categories
            }
        })
    
    async def check_setback_compliance(self, front_setback: float, side_setback: float, 
                                     rear_setback: float, property_lines: List[Dict] = None) -> Dict[str, Any]:
        """Check setback compliance in Revit"""
        return await self.send_request("tools/call", {
            "name": "check_setback_compliance",
            "arguments": {
                "front_setback": front_setback,
                "side_setback": side_setback,
                "rear_setback": rear_setback,
                "property_lines": property_lines or []
            }
        })
    
    async def create_compliance_report(self, project_name: str, building_type: str,
                                     check_categories: List[str] = None) -> Dict[str, Any]:
        """Create comprehensive compliance report"""
        if check_categories is None:
            check_categories = ["height", "setbacks", "fire_safety", "accessibility"]
        
        return await self.send_request("tools/call", {
            "name": "create_code_compliance_report",
            "arguments": {
                "project_name": project_name,
                "building_type": building_type,
                "check_categories": check_categories
            }
        })
    
    async def generate_revit_script(self, code_requirement: str, script_type: str = "python") -> Dict[str, Any]:
        """Generate Revit API script based on code requirements"""
        return await self.send_request("tools/call", {
            "name": "generate_revit_script",
            "arguments": {
                "code_requirement": code_requirement,
                "script_type": script_type
            }
        })
    
    async def process_natural_language_request(self, user_request: str) -> Dict[str, Any]:
        """Process natural language request and determine appropriate actions"""
        
        # Simple intent detection (you could use NLP models for more sophisticated parsing)
        request_lower = user_request.lower()
        
        if "height" in request_lower and ("limit" in request_lower or "restriction" in request_lower):
            # Extract height and zone information
            # This is a simplified parser - you'd want more robust NLP
            import re
            height_match = re.search(r'(\d+)\s*(?:feet|ft|\')', request_lower)
            zone_match = re.search(r'(r\d+|c\d+|m\d+)', request_lower)
            
            if height_match:
                height = float(height_match.group(1))
                zone = zone_match.group(1).upper() if zone_match else "R1"
                return await self.apply_height_restrictions(zone, height)
        
        elif "setback" in request_lower:
            # Extract setback information
            import re
            setback_matches = re.findall(r'(\d+)\s*(?:feet|ft|\')', request_lower)
            if len(setback_matches) >= 3:
                front, side, rear = [float(x) for x in setback_matches[:3]]
                return await self.check_setback_compliance(front, side, rear)
            elif len(setback_matches) == 1:
                # Assume uniform setback
                setback = float(setback_matches[0])
                return await self.check_setback_compliance(setback, setback, setback)
        
        elif "compliance" in request_lower and "report" in request_lower:
            # Extract project information
            project_match = re.search(r'project\s+(\w+)', request_lower)
            building_match = re.search(r'(residential|commercial|industrial|mixed)', request_lower)
            
            project_name = project_match.group(1) if project_match else "Current Project"
            building_type = building_match.group(1) if building_match else "residential"
            
            return await self.create_compliance_report(project_name, building_type)
        
        elif "script" in request_lower or "generate" in request_lower:
            # Generate custom script
            return await self.generate_revit_script(user_request)
        
        else:
            # Default to building code query
            return await self.query_building_codes(user_request)

class RevitAutomationHelper:
    """Helper class for Revit automation tasks"""
    
    def __init__(self, mcp_integration: MCPRevitIntegration):
        self.mcp = mcp_integration
        self.revit_scripts_dir = Path("revit_scripts")
        self.revit_scripts_dir.mkdir(exist_ok=True)
    
    def save_script_to_file(self, script_content: str, filename: str) -> Path:
        """Save generated script to file"""
        script_path = self.revit_scripts_dir / filename
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        logger.info(f"Script saved to {script_path}")
        return script_path
    
    async def execute_code_compliance_workflow(self, project_info: Dict[str, Any]) -> Dict[str, Any]:
        """Execute complete code compliance workflow"""
        results = {}
        
        try:
            # 1. Query relevant building codes
            query = f"{project_info.get('building_type', 'residential')} building code requirements {project_info.get('location', '')}"
            code_results = await self.mcp.query_building_codes(query)
            results['code_query'] = code_results
            
            # 2. Apply height restrictions if specified
            if 'max_height' in project_info and 'zone_type' in project_info:
                height_results = await self.mcp.apply_height_restrictions(
                    project_info['zone_type'],
                    project_info['max_height']
                )
                results['height_restrictions'] = height_results
            
            # 3. Check setbacks if specified
            if all(k in project_info for k in ['front_setback', 'side_setback', 'rear_setback']):
                setback_results = await self.mcp.check_setback_compliance(
                    project_info['front_setback'],
                    project_info['side_setback'],
                    project_info['rear_setback']
                )
                results['setback_compliance'] = setback_results
            
            # 4. Generate compliance report
            report_results = await self.mcp.create_compliance_report(
                project_info.get('project_name', 'Untitled Project'),
                project_info.get('building_type', 'residential')
            )
            results['compliance_report'] = report_results
            
            # 5. Save all generated scripts
            script_counter = 1
            for key, result in results.items():
                if 'script' in str(result).lower():
                    # Extract and save script content
                    script_filename = f"{project_info.get('project_name', 'project')}_{key}_{script_counter}.py"
                    # This would need script extraction logic
                    script_counter += 1
            
            return results
            
        except Exception as e:
            logger.error(f"Error in compliance workflow: {e}")
            return {"error": str(e)}
    
    def create_revit_macro(self, script_content: str, macro_name: str) -> str:
        """Create Revit macro wrapper for Python script"""
        macro_template = f'''
# Revit Macro: {macro_name}
# Generated by Building Code GPT

import clr
import sys

# Add references
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System')

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from System.Collections.Generic import List

def main():
    """Main macro function"""
    try:
        # Get current document
        doc = __revit__.ActiveUIDocument.Document
        
        # Execute the generated script
        {script_content}
        
    except Exception as e:
        TaskDialog.Show("Error", f"Macro execution failed: {{str(e)}}")

if __name__ == "__main__":
    main()
'''
        return macro_template

# Streamlit integration functions
def integrate_with_streamlit():
    """Integration functions for the Streamlit app"""
    
    import streamlit as st
    
    def add_mcp_sidebar():
        """Add MCP controls to Streamlit sidebar"""
        with st.sidebar:
            st.markdown("---")
            st.header("🔧 Revit Integration")
            
            # MCP connection status
            if 'mcp_integration' not in st.session_state:
                st.session_state.mcp_integration = MCPRevitIntegration()
            
            mcp = st.session_state.mcp_integration
            
            # Connection controls
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Connect MCP"):
                    if asyncio.run(mcp.start_server()):
                        st.success("MCP Connected!")
                    else:
                        st.error("MCP Connection Failed")
            
            with col2:
                if st.button("Disconnect"):
                    asyncio.run(mcp.stop_server())
                    st.info("MCP Disconnected")
            
            # Status indicator
            status = "🟢 Connected" if mcp.is_connected else "🔴 Disconnected"
            st.write(f"Status: {status}")
            
            # Quick actions
            st.subheader("Quick Actions")
            
            # Height restrictions
            with st.expander("Height Restrictions"):
                zone_type = st.selectbox("Zone Type", ["R1", "R2", "R3", "C1", "C2", "M1"])
                max_height = st.number_input("Max Height (ft)", min_value=1, value=35)
                if st.button("Apply Height Limit"):
                    if mcp.is_connected:
                        result = asyncio.run(mcp.apply_height_restrictions(zone_type, max_height))
                        st.write(result)
                    else:
                        st.warning("Please connect MCP first")
            
            # Setback compliance
            with st.expander("Setback Compliance"):
                front = st.number_input("Front Setback (ft)", min_value=0, value=20)
                side = st.number_input("Side Setback (ft)", min_value=0, value=10)
                rear = st.number_input("Rear Setback (ft)", min_value=0, value=15)
                if st.button("Check Setbacks"):
                    if mcp.is_connected:
                        result = asyncio.run(mcp.check_setback_compliance(front, side, rear))
                        st.write(result)
                    else:
                        st.warning("Please connect MCP first")
    
    def add_revit_commands_to_chat():
        """Add Revit-specific command processing to chat"""
        
        def process_revit_command(user_input: str) -> str:
            """Process user input for Revit commands"""
            
            # Check if input contains Revit-related keywords
            revit_keywords = [
                "apply height", "height restriction", "height limit",
                "setback", "compliance check", "building code",
                "generate script", "revit script", "automation"
            ]
            
            if any(keyword in user_input.lower() for keyword in revit_keywords):
                if 'mcp_integration' in st.session_state:
                    mcp = st.session_state.mcp_integration
                    if mcp.is_connected:
                        try:
                            result = asyncio.run(mcp.process_natural_language_request(user_input))
                            return f"Revit automation result: {result}"
                        except Exception as e:
                            return f"Error processing Revit command: {e}"
                    else:
                        return "Please connect to MCP server first to use Revit integration."
                else:
                    return "MCP integration not initialized. Please check the sidebar."
            
            return None  # Not a Revit command, process normally
        
        return process_revit_command

# Usage example and configuration
def setup_mcp_environment():
    """Setup MCP environment and dependencies"""
    
    # Create necessary directories
    directories = [
        "mcp",
        "revit_scripts", 
        "generated_scripts",
        "compliance_reports"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    # Create requirements file for MCP
    mcp_requirements = """
mcp>=1.0.0
asyncio-mqtt>=0.13.0
pydantic>=2.0.0
jsonschema>=4.0.0
"""
    
    with open("mcp_requirements.txt", "w") as f:
        f.write(mcp_requirements)
    
    # Create installation script
    install_script = """
@echo off
echo Installing MCP dependencies...
pip install -r mcp_requirements.txt
echo MCP setup complete!
pause
"""
    
    with open("install_mcp.bat", "w") as f:
        f.write(install_script)
    
    logger.info("MCP environment setup complete")

# Example usage
if __name__ == "__main__":
    # Setup environment
    setup_mcp_environment()
    
    # Example workflow
    async def example_workflow():
        mcp = MCPRevitIntegration()
        helper = RevitAutomationHelper(mcp)
        
        # Start MCP server
        await mcp.start_server()
        
        # Example project info
        project_info = {
            "project_name": "Sample_Building",
            "building_type": "residential",
            "zone_type": "R1",
            "max_height": 35,
            "front_setback": 20,
            "side_setback": 10,
            "rear_setback": 15,
            "location": "California"
        }
        
        # Execute workflow
        results = await helper.execute_code_compliance_workflow(project_info)
        print(f"Workflow results: {results}")
        
        # Stop server
        await mcp.stop_server()
    
    # Run example
    # asyncio.run(example_workflow())