from typing import Dict, Any, List
from langchain_core.messages import BaseMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from ..state import AgentState

class TableGeneratorNode:
    """
    Generates tabular data based on the extracted content and all available documents.
    """
    def __init__(self, llm):
        self.llm = llm
        self.parser = JsonOutputParser()
        self.prompt = PromptTemplate(
            template="""You are an expert at extracting and summarizing information into tabular format.
            Given the following documents and the current section content, generate relevant tabular data.
            The table should be in JSON format, with a 'title' and 'rows' key.
            Each row should be a dictionary where keys are column headers.

            All Documents:
            {documents}

            Current Section Title: {current_section}
            Current Section Content: {current_section_content}

            Instructions:
            - Identify key numerical or categorical data points relevant to the current section.
            - Create a table that summarizes this data.
            - Ensure the table is well-structured and easy to understand.
            - If no relevant tabular data can be extracted, return an empty table structure: {{"title": "", "rows": []}}.
            - The output MUST be a valid JSON object.

            Example Output:
            {{
                "title": "Financial Highlights Q1 2025",
                "rows": [
                    {{"Metric": "Revenue", "Value": "$10M", "Change": "+15%"}},
                    {{"Metric": "Profit", "Value": "$2M", "Change": "+20%"}}
                ]
            }}
            """,
            input_variables=["documents", "current_section", "current_section_content"],
        )
        self.chain = self.prompt | self.llm | self.parser

    def generate_table(self, state: AgentState) -> Dict[str, Any]:
        """
        Generates tabular data for the current section.
        """
        print(f"--- Generating table for section: '{state.get('current_section')}' ---")
        documents_content = "\n\n".join([doc["content"] for doc in state.get("documents", [])])
        current_section_content = state.get("current_section_content", "")
        current_section_title = state.get("current_section", "")

        try:
            tabular_data = self.chain.invoke({
                "documents": documents_content,
                "current_section": current_section_title,
                "current_section_content": current_section_content
            })
            print(f"--- Table generated for '{current_section_title}' ---")
            # Append the generated table to the current section's content or a new field
            # For now, let's add it to a new 'tabular_data' field in the state.
            # We might want to integrate this into 'completed_sections' later.
            
            # Update the current section in completed_sections with the new tabular data
            completed_sections = state.get("completed_sections", [])
            updated_completed_sections = []
            found = False
            for section in completed_sections:
                if section.get("section") == current_section_title:
                    section["tabular_data"] = tabular_data
                    found = True
                updated_completed_sections.append(section)
            
            if not found:
                # This case should ideally not happen if the flow is correct,
                # but as a fallback, create a new entry.
                updated_completed_sections.append({
                    "section": current_section_title,
                    "content": current_section_content,
                    "tabular_data": tabular_data,
                    "references": [] # Assuming references are handled by writer/extractor
                })

            return {"completed_sections": updated_completed_sections}

        except Exception as e:
            print(f"Error generating table for section '{current_section_title}': {e}")
            return {} # Return empty dict to avoid breaking the graph