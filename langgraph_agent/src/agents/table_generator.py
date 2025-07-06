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
            
            # Return the tabular_data and ensure other relevant state variables are passed through
            return {
                "tabular_data": tabular_data,
                "current_section_content": current_section_content, # Preserve content
                "current_section_references": state.get("current_section_references", []) # Preserve references
            }

        except Exception as e:
            print(f"Error generating table for section '{current_section_title}': {e}")
            import traceback
            traceback.print_exc()
            return {} # Return empty dict to avoid breaking the graph