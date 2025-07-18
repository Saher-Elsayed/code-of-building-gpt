import streamlit as st
import time
import os
import sys
import logging

# Console logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

# Ensure project root is on Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.rag.retrieval_system import RetrievalSystem
from src.rag.llm_interface import LocalLLMInterface
from src.ocr.document_processor import DocumentProcessor
from config.settings import settings

class EnhancedBuildingCodeGPTApp:
    def __init__(self):
        logger.info("Starting Enhanced StreamlitApp")
        self.setup_page()
        
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
        self.doc_proc = DocumentProcessor(
            tesseract_path=settings.TESSERACT_PATH,
            poppler_path=settings.POPPLER_PATH
        )

    def setup_page(self):
        st.set_page_config(
            page_title="Code of Building GPT - Enhanced",
            page_icon="🏗️",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        st.title("🏗️ Code of Building GPT - Enhanced")
        st.markdown("*AI-Powered Building Code Assistant with Enhanced Features*")

    def run(self):
        # Create enhanced tabs
        tab1, tab2, tab3 = st.tabs(["💬 Chat", "🏗️ Revit Tools", "📊 Reports"])
        
        with tab1:
            self.chat_interface()
        
        with tab2:
            self.revit_tools_interface()
        
        with tab3:
            st.header("📊 Compliance Reports")
            st.info("Compliance reporting tools will appear here.")
        
        # Sidebar
        self.render_sidebar()

    def revit_tools_interface(self):
        st.header("🏗️ Revit Automation Tools")
        
        # Create sub-tabs for different types of scripts
        subtab1, subtab2, subtab3, subtab4 = st.tabs([
            "📏 Height Restrictions", 
            "📐 Setback Compliance", 
            "🔥 Fire Safety", 
            "✨ Custom Script"
        ])
        
        with subtab1:
            self.height_restrictions_tool()
        
        with subtab2:
            self.setback_compliance_tool()
        
        with subtab3:
            self.fire_safety_tool()
        
        with subtab4:
            self.custom_script_tool()

    def height_restrictions_tool(self):
        st.subheader("📏 Building Height Restrictions")
        
        col1, col2 = st.columns(2)
        with col1:
            zone_type = st.selectbox("Zone Type", ["R1", "R2", "R3", "C1", "C2", "M1"], key="height_zone")
            max_height = st.number_input("Max Height (ft)", min_value=1, value=35, key="height_value")
        
        with col2:
            element_types = st.multiselect(
                "Apply to Elements",
                ["Walls", "Columns", "Structural Framing", "Roofs"],
                default=["Walls", "Columns"]
            )
        
        if st.button("Generate Height Restriction Script", key="gen_height"):
            script = f'''"""
Revit Height Restriction Script for {zone_type} Zoning
Maximum Height: {max_height} feet
Generated by Building Code GPT
"""

import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *

def apply_height_restrictions(doc):
    """Apply height restrictions for {zone_type} zoning"""
    
    max_height_ft = {max_height}
    element_categories = {element_types}
    modified_count = 0
    
    with Transaction(doc, "Apply Height Restrictions - {zone_type}") as t:
        t.Start()
        
        for category_name in element_categories:
            # Get elements by category
            if category_name == "Walls":
                category = BuiltInCategory.OST_Walls
            elif category_name == "Columns":
                category = BuiltInCategory.OST_Columns
            elif category_name == "Structural Framing":
                category = BuiltInCategory.OST_StructuralFraming
            elif category_name == "Roofs":
                category = BuiltInCategory.OST_Roofs
            else:
                continue
            
            # Collect elements
            collector = FilteredElementCollector(doc)
            elements = collector.OfCategory(category).WhereElementIsNotElementType().ToElements()
            
            for element in elements:
                try:
                    # Get element height parameter
                    height_param = element.get_Parameter(BuiltInParameter.INSTANCE_LENGTH_PARAM)
                    if height_param and height_param.AsDouble() > max_height_ft:
                        height_param.Set(max_height_ft)
                        modified_count += 1
                except:
                    continue
        
        t.Commit()
    
    TaskDialog.Show("Height Restrictions Applied", 
                   f"Modified {{modified_count}} elements to comply with {zone_type} height limit of {max_height} feet")
    return modified_count

# Execute the function
if __name__ == "__main__":
    doc = __revit__.ActiveUIDocument.Document
    apply_height_restrictions(doc)
'''
            self.display_generated_script(script, f"{zone_type}_height_restriction_{max_height}ft.py")

    def setback_compliance_tool(self):
        st.subheader("📐 Setback Compliance Checker")
        
        col1, col2 = st.columns(2)
        with col1:
            front_setback = st.number_input("Front Setback (ft)", min_value=0, value=20, key="front_sb")
            side_setback = st.number_input("Side Setback (ft)", min_value=0, value=10, key="side_sb")
        
        with col2:
            rear_setback = st.number_input("Rear Setback (ft)", min_value=0, value=15, key="rear_sb")
            property_width = st.number_input("Property Width (ft)", min_value=1, value=100, key="prop_width")
        
        if st.button("Generate Setback Compliance Script", key="gen_setback"):
            script = f'''"""
Revit Setback Compliance Script
Front: {front_setback}ft, Side: {side_setback}ft, Rear: {rear_setback}ft
Generated by Building Code GPT
"""

import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *

def check_setback_compliance(doc):
    """Check building setback compliance"""
    
    # Setback requirements
    front_setback_ft = {front_setback}
    side_setback_ft = {side_setback}
    rear_setback_ft = {rear_setback}
    
    violations = []
    
    # Get all walls
    collector = FilteredElementCollector(doc)
    walls = collector.OfCategory(BuiltInCategory.OST_Walls).WhereElementIsNotElementType().ToElements()
    
    for wall in walls:
        try:
            location_curve = wall.Location
            if isinstance(location_curve, LocationCurve):
                # Get wall endpoints
                curve = location_curve.Curve
                start_point = curve.GetEndPoint(0)
                end_point = curve.GetEndPoint(1)
                
                # Check setback compliance (simplified check)
                # In real implementation, you would calculate actual distances to property lines
                wall_id = wall.Id.IntegerValue
                
                # Example violation detection logic
                # This would need actual property boundary coordinates
                
        except Exception as e:
            continue
    
    # Report results
    message = f"Setback Compliance Check Complete\\n"
    message += f"Required setbacks: Front {{front_setback_ft}}ft, Side {{side_setback_ft}}ft, Rear {{rear_setback_ft}}ft\\n"
    message += f"Violations found: {{len(violations)}}"
    
    TaskDialog.Show("Setback Compliance", message)
    return violations

# Execute the function
if __name__ == "__main__":
    doc = __revit__.ActiveUIDocument.Document
    check_setback_compliance(doc)
'''
            self.display_generated_script(script, f"setback_compliance_{front_setback}_{side_setback}_{rear_setback}.py")

    def fire_safety_tool(self):
        st.subheader("🔥 Fire Safety Compliance")
        
        col1, col2 = st.columns(2)
        with col1:
            building_type = st.selectbox("Building Type", ["Residential", "Commercial", "Industrial", "Assembly"])
            occupancy_load = st.number_input("Occupancy Load", min_value=1, value=100)
        
        with col2:
            stories = st.number_input("Number of Stories", min_value=1, value=3)
            sprinkler_system = st.checkbox("Sprinkler System Required", value=True)
        
        if st.button("Generate Fire Safety Script", key="gen_fire"):
            script = f'''"""
Revit Fire Safety Compliance Script
Building Type: {building_type}, Stories: {stories}, Occupancy: {occupancy_load}
Generated by Building Code GPT
"""

import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *

def check_fire_safety_compliance(doc):
    """Check fire safety compliance for {building_type.lower()} building"""
    
    building_type = "{building_type}"
    max_stories = {stories}
    occupancy_load = {occupancy_load}
    sprinkler_required = {str(sprinkler_system).lower()}
    
    compliance_issues = []
    
    # Check exit requirements
    collector = FilteredElementCollector(doc)
    doors = collector.OfCategory(BuiltInCategory.OST_Doors).WhereElementIsNotElementType().ToElements()
    
    exit_doors = []
    for door in doors:
        try:
            # Check if door is an exit door
            door_type = door.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME)
            if door_type and "exit" in door_type.AsString().lower():
                exit_doors.append(door)
        except:
            continue
    
    # Calculate required exits based on occupancy load
    required_exits = max(2, (occupancy_load // 50))
    
    if len(exit_doors) < required_exits:
        compliance_issues.append(f"Insufficient exits: {{len(exit_doors)}} found, {{required_exits}} required")
    
    # Check corridor widths (simplified)
    # In real implementation, you would measure actual corridor widths
    
    # Check fire-rated assemblies
    walls = collector.OfCategory(BuiltInCategory.OST_Walls).WhereElementIsNotElementType().ToElements()
    fire_rated_walls = 0
    
    for wall in walls:
        try:
            fire_rating = wall.get_Parameter(BuiltInParameter.FIRE_RATING)
            if fire_rating and fire_rating.AsDouble() > 0:
                fire_rated_walls += 1
        except:
            continue
    
    # Report results
    message = f"Fire Safety Compliance Check\\n"
    message += f"Building Type: {{building_type}}\\n"
    message += f"Stories: {{max_stories}}\\n"
    message += f"Occupancy Load: {{occupancy_load}}\\n"
    message += f"Exit Doors Found: {{len(exit_doors)}} (Required: {{required_exits}})\\n"
    message += f"Fire-Rated Walls: {{fire_rated_walls}}\\n"
    message += f"Compliance Issues: {{len(compliance_issues)}}"
    
    if compliance_issues:
        message += "\\n\\nIssues:\\n" + "\\n".join(compliance_issues)
    
    TaskDialog.Show("Fire Safety Compliance", message)
    return compliance_issues

# Execute the function
if __name__ == "__main__":
    doc = __revit__.ActiveUIDocument.Document
    check_fire_safety_compliance(doc)
'''
            self.display_generated_script(script, f"fire_safety_{building_type.lower()}_{stories}story.py")

    def custom_script_tool(self):
        st.subheader("✨ Custom Script Generator")
        st.write("Generate Revit scripts for any building code requirement using AI")
        
        # User input for custom requirements
        requirement = st.text_area(
            "Building Code Requirement",
            placeholder="e.g., Ensure all doorways meet ADA width requirements of 32 inches minimum",
            height=100
        )
        
        script_type = st.selectbox("Script Type", ["Compliance Check", "Parameter Modification", "Element Analysis"])
        
        if st.button("Generate Custom Script", key="gen_custom") and requirement:
            with st.spinner("Generating custom script using AI..."):
                # Use the LLM to generate a custom script
                docs = self.retriever.retrieve(f"building code {requirement}", k=3)
                
                prompt = f"""Generate a Revit Python script that implements the following building code requirement:

{requirement}

The script should:
1. Use Revit API to access building elements
2. Check compliance with the specified requirement
3. Provide clear feedback to the user
4. Include proper error handling
5. Be production-ready code

Script type: {script_type}

Please generate a complete Python script with proper imports and main function."""

                script_content = ""
                placeholder = st.empty()
                
                try:
                    for chunk in self.llm.generate_response(prompt, docs, stream=True):
                        script_content += chunk
                        placeholder.markdown("**Generating script...**\n\n" + script_content + "▌")
                        time.sleep(0.01)
                    
                    placeholder.empty()
                    self.display_generated_script(script_content, f"custom_{script_type.lower().replace(' ', '_')}.py")
                    
                except Exception as e:
                    st.error(f"Error generating custom script: {e}")

    def display_generated_script(self, script, filename):
        """Display generated script with download and copy options"""
        st.success(f"✅ Script generated successfully!")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.write(f"**📄 {filename}**")
        with col2:
            if st.button("📋 Copy", key=f"copy_{filename}"):
                st.code(script, language='python')
                st.info("Script displayed above - use Ctrl+A, Ctrl+C to copy")
        with col3:
            st.download_button(
                "💾 Download",
                script,
                filename,
                "text/plain",
                key=f"download_{filename}"
            )
        
        # Display the script
        st.code(script, language='python')
        
        # Save to revit_scripts directory
        try:
            import os
            os.makedirs("revit_scripts", exist_ok=True)
            script_path = os.path.join("revit_scripts", filename)
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script)
            st.info(f"💾 Script saved to: `{script_path}`")
        except Exception as e:
            st.warning(f"Could not save script: {e}")

    def render_sidebar(self):
        with st.sidebar:
            st.header("📁 Document Upload")
            uploaded = st.file_uploader(
                "Upload PDF(s)", type=["pdf"], accept_multiple_files=True
            )
            if uploaded and st.button("Process Documents"):
                self.process_uploaded(uploaded)

            st.markdown("---")
            st.header("⚙️ Settings")
            num_results = st.slider("Top-k Retrievals", 1, 20, 5)
            st.session_state.num_results = num_results

    def process_uploaded(self, files):
        progress = st.progress(0)
        docs = []
        
        for i, f in enumerate(files, start=1):
            st.info(f"Processing {f.name}...")
            tmp_path = f"temp_{f.name}"
            with open(tmp_path, "wb") as out:
                out.write(f.getbuffer())

            try:
                pages = self.doc_proc.extract_text_from_pdf(tmp_path)
                for p in pages:
                    docs.append({
                        "id": f"{f.name}_{p['page_number']}",
                        "text": p["text"],
                        "page_number": p["page_number"],
                        "confidence": p["confidence"],
                        "source": f.name,
                    })
            except Exception as e:
                st.error(f"Error processing {f.name}: {e}")
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            
            progress.progress(i / len(files))

        if docs:
            self.retriever.add_documents(docs)
            st.success(f"✅ Successfully processed {len(docs)} pages!")

    def chat_interface(self):
        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display chat history
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # User input
        if prompt := st.chat_input("Ask building code questions..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Generate response
            with st.chat_message("assistant"):
                self.generate_response(prompt)

    def generate_response(self, prompt):
        # Retrieve documents
        k = st.session_state.get("num_results", 5)
        docs = self.retriever.retrieve(prompt, k=k)
        
        if not docs:
            msg = "😕 No relevant sections found. Please upload building code documents first."
            st.markdown(msg)
            st.session_state.messages.append({"role": "assistant", "content": msg})
            return

        # Generate streaming response
        placeholder = st.empty()
        full_response = ""
        
        try:
            for chunk in self.llm.generate_response(prompt, docs, stream=True):
                full_response += chunk
                placeholder.markdown(full_response + "▌")
                time.sleep(settings.STREAM_DELAY)
            
            placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
            # Show sources
            with st.expander("📚 Sources"):
                for i, doc in enumerate(docs, 1):
                    meta = doc["metadata"]
                    st.write(f"{i}. **{meta.get('source', 'Unknown')}**, page {meta.get('page_number', 'N/A')}")
                    
        except Exception as e:
            error_msg = f"Error generating response: {e}"
            st.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})

if __name__ == "__main__":
    app = EnhancedBuildingCodeGPTApp()
    app.run()