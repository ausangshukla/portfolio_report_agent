from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import BaseMessage
from ..state import AgentState # Assuming AgentState is in src/state.py

class ExtractorNode:
    """
    The ExtractorNode is responsible for performing an initial extraction of information
    for a given section from the loaded documents. It generates a first draft of the
    section content and identifies relevant references.
    """
    def __init__(self, llm):
        """
        Initializes the ExtractorNode with a language model.

        Args:
            llm: An instance of a LangChain-compatible language model.
        """
        self.llm = llm
        self.parser = JsonOutputParser()
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert financial analyst. Your task is to extract
             relevant information from the provided documents to create a draft for the
             "{section_title}" section of a portfolio analysis report.

             Focus on extracting factual information and key insights.
             Also, identify the source document and page/row number for each piece of information.
             If content is from a CSV, specify the filename and row number.
             If content is from a PDF/TXT/DOCX, specify the filename and page number.
             
             **IMPORTANT**: Always include a 'content' key in your JSON output. If no relevant information is found, set 'content' to "No information found for this section.".
             
             {format_instructions}
             """),
            ("user", "Documents:\n{documents}\n\nSection Title: {section_title}\n{section_instruction}")
        ])
        self.chain = self.prompt | self.llm | self.parser
 
    def extract(self, state: AgentState) -> Dict[str, Any]:
        """
        Extracts information for the current section from the documents.
 
        Args:
            state (AgentState): The current state of the agent.
 
        Returns:
            Dict[str, Any]: A dictionary containing the updated state with the
                            extracted section content and references.
        """
        current_section_title = state.get("current_section")
        current_section_instruction = state.get("current_section_instruction", "")
        documents = state.get("documents")
 
        if not current_section_title:
            raise ValueError("No current section title specified in the agent state.")
        if not documents:
            raise ValueError("No documents available in the agent state for extraction.")
 
        # Format documents for the prompt
        formatted_documents = "\n".join([
            f"--- Document: {doc.get('filename', 'N/A')} ---\n"
            f"{doc.get('content', 'Content not available')}"
            for doc in documents
        ])
 
        print(f"--- ExtractorNode: Extracting for section '{current_section_title}' ---")
        print(f"ExtractorNode: Input documents for '{current_section_title}':\n{formatted_documents[:500]}...") # Log first 500 chars of documents
 
        try:
            # Invoke the LLM chain to get the extracted content and references
            extraction_input = {
                "section_title": current_section_title,
                "documents": formatted_documents,
                "section_instruction": current_section_instruction,
                "format_instructions": self.parser.get_format_instructions() # Pass format instructions
            }
            print(f"ExtractorNode: Invoking LLM with input for '{current_section_title}': {extraction_input['section_title']}")
            
            raw_llm_output = self.llm.invoke(self.prompt.format_messages(**extraction_input))
            print(f"ExtractorNode: Raw LLM output for '{current_section_title}': {raw_llm_output}") # Log raw LLM output
 
            # Clean the raw LLM output by removing markdown code block delimiters
            cleaned_output = raw_llm_output.content.strip()
            if cleaned_output.startswith("```json") and cleaned_output.endswith("```"):
                cleaned_output = cleaned_output[len("```json"): -len("```")].strip()
            elif cleaned_output.startswith("```") and cleaned_output.endswith("```"):
                cleaned_output = cleaned_output[len("```"): -len("```")].strip()
 
            print(f"--- Debug: Cleaned LLM output for ExtractorNode: {cleaned_output} ---") # New debug print
 
            # Parse the cleaned output
            extraction_result = self.parser.parse(cleaned_output)
 
            # Ensure the output matches the expected JSON structure
            content = extraction_result.get("content", "")
            references = extraction_result.get("references", [])
 
            # Update the state with the extracted content and references
            return {
                "current_section_content": content,
                "current_section_references": references,
                "messages": state.get("messages", []) + [
                    BaseMessage(content=f"ExtractorNode: Initial draft for '{current_section_title}' created.", type="tool_output")
                ]
            }
        except Exception as e:
            error_message = f"ExtractorNode: Error during extraction for '{current_section_title}': {e}"
            print(error_message)
            return {
                "messages": state.get("messages", []) + [
                    BaseMessage(content=error_message, type="error")
                ]
            }
 
# Example Usage (for testing purposes)
if __name__ == "__main__":
    from langchain_community.llms import FakeListLLM
    from ..state import AgentState
 
    # Mock LLM for testing
    mock_llm = FakeListLLM(responses=[
        '{"content": "This is an overview of the company from doc1.", "references": [{"document": "doc1.txt", "location": "page 1"}]}',
        '{"content": "Financials show revenue of $10M from doc2.", "references": [{"document": "doc2.csv", "location": "row 5"}]}'
    ])
 
    extractor = ExtractorNode(llm=mock_llm)
 
    # Mock initial state
    initial_state: AgentState = {
        "documents": [
            {"filename": "doc1.txt", "content": "Company overview: This is a test document for company A."},
            {"filename": "doc2.csv", "content": "Revenue,Profit\n10M,2M\n12M,3M"}
        ],
        "sections_to_process": [{"title": "Overview", "instruction": "Be concise."}, {"title": "Financial Review", "instruction": "Focus on growth."}],
        "completed_sections": [],
        "current_section": "Overview",
        "current_section_instruction": "Be concise.",
        "loop_count": 0,
        "critique": None,
        "messages": []
    }
 
    print("\n--- Running ExtractorNode for 'Overview' ---")
    updated_state = extractor.extract(initial_state)
    print("Updated State:")
    print(updated_state["completed_sections"])
    print(updated_state["messages"])
 
    # Simulate processing the next section
    initial_state["current_section"] = "Financial Review"
    initial_state["current_section_instruction"] = "Focus on growth."
    initial_state["completed_sections"] = [] # Reset for this example
    print("\n--- Running ExtractorNode for 'Financial Review' ---")
    updated_state_financial = extractor.extract(initial_state)
    print("Updated State:")
    print(updated_state_financial["completed_sections"])
    print(updated_state_financial["messages"])