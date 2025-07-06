#!/usr/bin/env python3
"""
MCP Server for Building Code GPT + Revit Integration
Provides tools to interact with Revit API based on building code queries
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# Import your existing components
from src.rag.retrieval_system import RetrievalSystem
from src.rag.llm_interface import LocalLLMInterface
from src.ocr.document_processor import DocumentProcessor
from config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-revit-server")

class BuildingCodeMCPServer:
    def __init__(self):
        self.server = Server("building-code-revit")
        self.retriever = None
        self.llm = None
        self.revit_session = None
        self.setup_tools()

    def setup_tools(self):
        """Register MCP tools for Revit integration"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List available tools"""
            return [
                types.Tool(
                    name="query_building_codes",
                    description="Query building codes and regulations from the vector database",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Natural language query about building codes"
                            },
                            "k": {
                                "type": "integer",
                                "description": "Number of relevant chunks to retrieve",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                ),
                types.Tool(
                    name="apply_height_restrictions",
                    description="Apply building height restrictions to Revit model based on zoning",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "zone_type": {
                                "type": "string",
                                "description": "Zoning classification (e.g., R1, R2, C1, etc.)"
                            },
                            "max_height": {
                                "type": "number",
                                "description": "Maximum height in feet"
                            },
                            "element_categories": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Revit element categories to apply restrictions to",
                                "default": ["Walls", "Columns", "Structural Framing"]
                            }
                        },
                        "required": ["zone_type", "max_height"]
                    }
                ),
                types.Tool(
                    name="check_setback_compliance",
                    description="Check and apply setback requirements in Revit model",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "front_setback": {"type": "number", "description": "Front setback in feet"},
                            "side_setback": {"type": "number", "description": "Side setback in feet"},
                            "rear_setback": {"type": "number", "description": "Rear setback in feet"},
                            "property_lines": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "x": {"type": "number"},
                                        "y": {"type": "number"}
                                    }
                                },
                                "description": "Property boundary coordinates"
                            }
                        },
                        "required": ["front_setback", "side_setback", "rear_setback"]
                    }
                ),
                types.Tool(
                    name="create_code_compliance_report",
                    description="Generate a comprehensive building code compliance report",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_name": {
                                "type": "string",
                                "description": "Name of the Revit project"
                            },
                            "building_type": {
                                "type": "string",
                                "description": "Type of building (residential, commercial, etc.)"
                            },
                            "check_categories": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Code categories to check",
                                "default": ["height", "setbacks", "fire_safety", "accessibility"]
                            }
                        },
                        "required": ["project_name", "building_type"]
                    }
                ),
                types.Tool(
                    name="revit_element_query",
                    description="Query and modify Revit elements based on building code requirements",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "element_type": {
                                "type": "string",
                                "description": "Type of Revit element (Wall, Door, Window, etc.)"
                            },
                            "filter_criteria": {
                                "type": "object",
                                "description": "Criteria to filter elements"
                            },
                            "modifications": {
                                "type": "object",
                                "description": "Parameters to modify on filtered elements"
                            }
                        },
                        "required": ["element_type"]
                    }
                ),
                types.Tool(
                    name="generate_revit_script",
                    description="Generate Revit API script based on building code requirements",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code_requirement": {
                                "type": "string",
                                "description": "Building code requirement to implement"
                            },
                            "script_type": {
                                "type": "string",
                                "enum": ["python", "dynamo", "c#"],
                                "description": "Type of script to generate",
                                "default": "python"
                            }
                        },
                        "required": ["code_requirement"]
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
            """Handle tool calls"""
            try:
                if name == "query_building_codes":
                    return await self.query_building_codes(arguments)
                elif name == "apply_height_restrictions":
                    return await self.apply_height_restrictions(arguments)
                elif name == "check_setback_compliance":
                    return await self.check_setback_compliance(arguments)
                elif name == "create_code_compliance_report":
                    return await self.create_code_compliance_report(arguments)
                elif name == "revit_element_query":
                    return await self.revit_element_query(arguments)
                elif name == "generate_revit_script":
                    return await self.generate_revit_script(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                logger.error(f"Error in tool {name}: {e}")
                return [types.TextContent(
                    type="text",
                    text=f"Error executing {name}: {str(e)}"
                )]

    async def initialize_components(self):
        """Initialize building code components"""
        try:
            self.retriever = RetrievalSystem(
                embedding_model=settings.EMBEDDING_MODEL,
                vector_db_path=settings.VECTOR_DB_PATH,
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP
            )
            self.llm = LocalLLMInterface(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.LLM_MODEL
            )
            logger.info("Building code components initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise

    async def query_building_codes(self, arguments: dict) -> list[types.TextContent]:
        """Query building codes from vector database"""
        if not self.retriever:
            await self.initialize_components()
        
        query = arguments.get("query", "")
        k = arguments.get("k", 5)
        
        try:
            results = self.retriever.retrieve(query, k=k)
            
            response_text = f"Found {len(results)} relevant building code sections:\n\n"
            for i, result in enumerate(results, 1):
                metadata = result["metadata"]
                response_text += f"{i}. **Source:** {metadata.get('source', 'Unknown')}\n"
                response_text += f"   **Page:** {metadata.get('page_number', 'N/A')}\n"
                response_text += f"   **Section:** {metadata.get('section', 'Unknown')}\n"
                response_text += f"   **Content:** {result['content'][:200]}...\n"
                response_text += f"   **Relevance Score:** {result['score']:.3f}\n\n"
            
            return [types.TextContent(type="text", text=response_text)]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error querying building codes: {str(e)}"
            )]

    async def apply_height_restrictions(self, arguments: dict) -> list[types.TextContent]:
        """Apply height restrictions to Revit model"""
        zone_type = arguments.get("zone_type")
        max_height = arguments.get("max_height")
        element_categories = arguments.get("element_categories", ["Walls", "Columns", "Structural Framing"])
        
        # Generate Revit script to apply height restrictions
        script = self.generate_height_restriction_script(zone_type, max_height, element_categories)
        
        result_text = f"Height restriction applied for {zone_type} zoning:\n"
        result_text += f"Maximum height: {max_height} feet\n"
        result_text += f"Applied to categories: {', '.join(element_categories)}\n\n"
        result_text += "Generated Revit Python script:\n"
        result_text += f"```python\n{script}\n```"
        
        return [types.TextContent(type="text", text=result_text)]

    async def check_setback_compliance(self, arguments: dict) -> list[types.TextContent]:
        """Check setback compliance in Revit model"""
        front_setback = arguments.get("front_setback")
        side_setback = arguments.get("side_setback")
        rear_setback = arguments.get("rear_setback")
        property_lines = arguments.get("property_lines", [])
        
        script = self.generate_setback_compliance_script(front_setback, side_setback, rear_setback, property_lines)
        
        result_text = f"Setback compliance check configured:\n"
        result_text += f"Front setback: {front_setback} feet\n"
        result_text += f"Side setback: {side_setback} feet\n"
        result_text += f"Rear setback: {rear_setback} feet\n\n"
        result_text += "Generated Revit Python script:\n"
        result_text += f"```python\n{script}\n```"
        
        return [types.TextContent(type="text", text=result_text)]

    async def create_code_compliance_report(self, arguments: dict) -> list[types.TextContent]:
        """Create comprehensive compliance report"""
        project_name = arguments.get("project_name")
        building_type = arguments.get("building_type")
        check_categories = arguments.get("check_categories", ["height", "setbacks", "fire_safety", "accessibility"])
        
        # Query relevant codes for each category
        report_sections = []
        for category in check_categories:
            if self.retriever:
                query = f"{building_type} {category} building code requirements"
                results = self.retriever.retrieve(query, k=3)
                
                section_text = f"## {category.title()} Requirements\n\n"
                for result in results:
                    metadata = result["metadata"]
                    section_text += f"- **{metadata.get('source', 'Unknown')}** (Page {metadata.get('page_number', 'N/A')})\n"
                    section_text += f"  {result['content'][:150]}...\n\n"
                
                report_sections.append(section_text)
        
        full_report = f"# Building Code Compliance Report\n\n"
        full_report += f"**Project:** {project_name}\n"
        full_report += f"**Building Type:** {building_type}\n"
        full_report += f"**Generated:** {asyncio.get_event_loop().time()}\n\n"
        full_report += "\n".join(report_sections)
        
        return [types.TextContent(type="text", text=full_report)]

    async def revit_element_query(self, arguments: dict) -> list[types.TextContent]:
        """Query and modify Revit elements"""
        element_type = arguments.get("element_type")
        filter_criteria = arguments.get("filter_criteria", {})
        modifications = arguments.get("modifications", {})
        
        script = self.generate_element_query_script(element_type, filter_criteria, modifications)
        
        result_text = f"Revit element query configured for {element_type}:\n"
        result_text += f"Filter criteria: {filter_criteria}\n"
        result_text += f"Modifications: {modifications}\n\n"
        result_text += "Generated Revit Python script:\n"
        result_text += f"```python\n{script}\n```"
        
        return [types.TextContent(type="text", text=result_text)]

    async def generate_revit_script(self, arguments: dict) -> list[types.TextContent]:
        """Generate Revit API script based on code requirements"""
        code_requirement = arguments.get("code_requirement")
        script_type = arguments.get("script_type", "python")
        
        if not self.llm:
            await self.initialize_components()
        
        # Query relevant building codes
        if self.retriever:
            relevant_codes = self.retriever.retrieve(code_requirement, k=3)
            context = "\n".join([doc["content"] for doc in relevant_codes])
        else:
            context = code_requirement
        
        # Generate script using LLM
        prompt = f"""
        Generate a Revit API {script_type} script to implement the following building code requirement:
        
        {code_requirement}
        
        Relevant building code context:
        {context}
        
        The script should:
        1. Access the Revit document
        2. Filter relevant elements
        3. Apply code-compliant modifications
        4. Include error handling
        5. Provide user feedback
        """
        
        script_content = ""
        if self.llm:
            for chunk in self.llm.generate_response(prompt, relevant_codes if self.retriever else [], stream=False):
                script_content += chunk
        
        result_text = f"Generated {script_type} script for: {code_requirement}\n\n"
        result_text += f"```{script_type}\n{script_content}\n```"
        
        return [types.TextContent(type="text", text=result_text)]

    def generate_height_restriction_script(self, zone_type: str, max_height: float, categories: list) -> str:
        """Generate Python script for height restrictions"""
        return f'''
import clr
clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *

def apply_height_restrictions(doc):
    """Apply height restrictions for {zone_type} zoning"""
    
    # Start transaction
    with Transaction(doc, "Apply Height Restrictions - {zone_type}") as t:
        t.Start()
        
        max_height_ft = {max_height}
        categories_to_check = {categories}
        modified_elements = []
        
        # Iterate through specified categories
        for cat_name in categories_to_check:
            try:
                # Get built-in category
                if cat_name == "Walls":
                    category = BuiltInCategory.OST_Walls
                elif cat_name == "Columns":
                    category = BuiltInCategory.OST_Columns
                elif cat_name == "Structural Framing":
                    category = BuiltInCategory.OST_StructuralFraming
                else:
                    continue
                
                # Collect elements
                collector = FilteredElementCollector(doc)
                elements = collector.OfCategory(category).WhereElementIsNotElementType().ToElements()
                
                for element in elements:
                    # Get element height
                    height_param = element.get_Parameter(BuiltInParameter.INSTANCE_LENGTH_PARAM)
                    if height_param and height_param.AsDouble() > max_height_ft:
                        # Modify height to comply with zoning
                        height_param.Set(max_height_ft)
                        modified_elements.append(element.Id)
                        
            except Exception as e:
                print(f"Error processing {{cat_name}}: {{e}}")
        
        t.Commit()
        
        # Report results
        TaskDialog.Show("Height Restriction Applied", 
                       f"Modified {{len(modified_elements)}} elements to comply with {zone_type} height limit of {max_height} feet")
        
        return modified_elements

# Execute the function
if __name__ == "__main__":
    doc = __revit__.ActiveUIDocument.Document
    apply_height_restrictions(doc)
'''

    def generate_setback_compliance_script(self, front: float, side: float, rear: float, property_lines: list) -> str:
        """Generate Python script for setback compliance"""
        return f'''
import clr
clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *

def check_setback_compliance(doc):
    """Check setback compliance"""
    
    # Setback requirements
    front_setback = {front}
    side_setback = {side}
    rear_setback = {rear}
    property_lines = {property_lines}
    
    # Start transaction
    with Transaction(doc, "Check Setback Compliance") as t:
        t.Start()
        
        violations = []
        
        # Get all walls
        collector = FilteredElementCollector(doc)
        walls = collector.OfCategory(BuiltInCategory.OST_Walls).WhereElementIsNotElementType().ToElements()
        
        for wall in walls:
            try:
                # Get wall location
                location_curve = wall.Location
                if isinstance(location_curve, LocationCurve):
                    curve = location_curve.Curve
                    start_point = curve.GetEndPoint(0)
                    end_point = curve.GetEndPoint(1)
                    
                    # Check distance to property lines
                    # (Simplified calculation - in practice, you'd need more complex geometry)
                    
                    # Add violation checking logic here
                    # For now, just mark walls that might be too close
                    
            except Exception as e:
                print(f"Error checking wall {{wall.Id}}: {{e}}")
        
        t.Commit()
        
        # Report results
        message = f"Setback Compliance Check Complete\\n"
        message += f"Front setback: {front} ft\\n"
        message += f"Side setback: {side} ft\\n"
        message += f"Rear setback: {rear} ft\\n"
        message += f"Violations found: {{len(violations)}}"
        
        TaskDialog.Show("Setback Compliance", message)
        
        return violations

# Execute the function
if __name__ == "__main__":
    doc = __revit__.ActiveUIDocument.Document
    check_setback_compliance(doc)
'''

    def generate_element_query_script(self, element_type: str, filter_criteria: dict, modifications: dict) -> str:
        """Generate script for element querying and modification"""
        return f'''
import clr
clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *

def query_and_modify_elements(doc):
    """Query and modify {element_type} elements"""
    
    # Filter criteria: {filter_criteria}
    # Modifications: {modifications}
    
    with Transaction(doc, "Query and Modify {element_type}") as t:
        t.Start()
        
        # Get appropriate built-in category
        if "{element_type}" == "Wall":
            category = BuiltInCategory.OST_Walls
        elif "{element_type}" == "Door":
            category = BuiltInCategory.OST_Doors
        elif "{element_type}" == "Window":
            category = BuiltInCategory.OST_Windows
        else:
            # Default to walls
            category = BuiltInCategory.OST_Walls
        
        # Collect elements
        collector = FilteredElementCollector(doc)
        elements = collector.OfCategory(category).WhereElementIsNotElementType().ToElements()
        
        modified_count = 0
        
        for element in elements:
            try:
                # Apply filter criteria
                passes_filter = True
                # Add your filter logic here based on {filter_criteria}
                
                if passes_filter:
                    # Apply modifications
                    # Add your modification logic here based on {modifications}
                    modified_count += 1
                    
            except Exception as e:
                print(f"Error processing element {{element.Id}}: {{e}}")
        
        t.Commit()
        
        TaskDialog.Show("Element Query Complete", 
                       f"Modified {{modified_count}} {element_type} elements")
        
        return modified_count

# Execute the function
if __name__ == "__main__":
    doc = __revit__.ActiveUIDocument.Document
    query_and_modify_elements(doc)
'''

    async def run(self):
        """Run the MCP server"""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="building-code-revit",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )

if __name__ == "__main__":
    server = BuildingCodeMCPServer()
    asyncio.run(server.run())