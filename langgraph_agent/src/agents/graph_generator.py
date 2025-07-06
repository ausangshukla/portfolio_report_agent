from typing import Dict, Any, List
from langchain_core.messages import BaseMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from ..state import AgentState

class GraphGeneratorNode:
    """
    Generates graph specifications (e.g., for D3.js, Chart.js, or a simple textual description)
    based on the extracted content and all available documents.
    """
    def __init__(self, llm):
        self.llm = llm
        self.parser = JsonOutputParser()
        self.prompt = PromptTemplate(
            template="""You are an expert at identifying and summarizing data suitable for graphical representation.
            Given the following documents and the current section content, identify key data points
            that can be visualized and propose a suitable graph type and its data structure.
            The output should be a JSON object with a 'title', 'type' (e.g., 'bar', 'line', 'pie', 'textual_description'),
            and 'data' key. The 'data' key should contain the necessary data for the graph.
            If a textual description is more appropriate, set 'type' to 'textual_description' and
            provide a clear description in the 'data' field.

            All Documents:
            {documents}

            Current Section Title: {current_section}
            Current Section Content: {current_section_content}
            Tabular Data for Current Section (if available): {tabular_data}

            Instructions:
            - Analyze the content and tabular data for trends, comparisons, or distributions.
            - Suggest a graph type that best represents the identified data.
            - Provide the data in a structured format suitable for the chosen graph type.
            - If no suitable data for a graph is found, return an empty graph structure: {{"title": "", "type": "none", "data": {{}}}}.
            - The output MUST be a valid JSON object.

            Example Output (Bar Chart):
            {{
                "title": "Quarterly Revenue Comparison",
                "type": "bar",
                "data": {{
                    "labels": ["Q1", "Q2", "Q3", "Q4"],
                    "datasets": [
                        {{"label": "Revenue", "data": [100, 120, 150, 130]}}
                    ]
                }}
            }}

            Example Output (Textual Description):
            {{
                "title": "Key Performance Indicators Overview",
                "type": "textual_description",
                "data": "The company has shown consistent growth in revenue over the last three quarters, with a slight dip in Q4 due to seasonal factors. Profit margins have remained stable."
            }}
            """,
            input_variables=["documents", "current_section", "current_section_content", "tabular_data"],
        )
        self.chain = self.prompt | self.llm | self.parser

    def generate_graph(self, state: AgentState) -> Dict[str, Any]:
        """
        Generates graph specifications for the current section.
        """
        print(f"--- Generating graph for section: '{state.get('current_section')}' ---")
        documents_content = "\n\n".join([doc["content"] for doc in state.get("documents", [])])
        current_section_content = state.get("current_section_content", "")
        current_section_title = state.get("current_section", "")
        tabular_data = state.get("tabular_data", {}) # Get tabular data if available
        current_section_references = state.get("current_section_references", []) # Get references from writer

        try:
            graph_spec = self.chain.invoke({
                "documents": documents_content,
                "current_section": current_section_title,
                "current_section_content": current_section_content,
                "tabular_data": tabular_data
            })
            print(f"--- Graph spec generated for '{current_section_title}' ---")
            
            # Update the current section in completed_sections with the new graph spec
            # Create the new completed section entry
            new_completed_section = {
                "section": current_section_title,
                "content": current_section_content,
                "graph_spec": graph_spec,
                "references": current_section_references # Use references from writer
            }

            # Append the new completed section to the list
            completed_sections = state.get("completed_sections", []) + [new_completed_section]

            return {"completed_sections": completed_sections}

        except Exception as e:
            print(f"Error generating graph for section '{current_section_title}': {e}")
            return {} # Return empty dict to avoid breaking the graph