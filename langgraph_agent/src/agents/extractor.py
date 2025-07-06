from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import BaseMessage
from langchain_core.pydantic_v1 import BaseModel, Field
from ..state import AgentState # Assuming AgentState is in src/state.py

class SubSection(BaseModel):
    title: str = Field(description="The title of the sub-section.")
    content: str = Field(description="The content of the sub-section.")

class ExtractedSection(BaseModel):
    sub_sections: List[SubSection] = Field(description="A list of sub-sections within the main section.")

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
        self.parser = JsonOutputParser(pydantic_object=ExtractedSection)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert financial analyst. Your task is to extract
             relevant information from the provided documents to create a draft for the
             "{section_title}" section of a portfolio analysis report.

             Focus on extracting factual information and key insights.
             Break down the content into logical sub-sections, each with a clear title and its corresponding content.
             
             IMPORTANT: Always include a 'sub_sections' key in your JSON output, which should be a list of sub-section objects. If no relevant information is found for a sub-section, its content should be "No information found for this sub-section.". If no sub-sections can be created, return an empty list for 'sub_sections'. No markdown in the json output.
             
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
            sub_sections = extraction_result.get("sub_sections", [])
            
            # Convert sub_sections to a single content string for now, or pass as is if the next node can handle it
            # For now, let's convert it to a string, but ideally, the next node should handle the structured data.
            # If the next node (reviewer/writer) expects a single string, we need to format it here.
            # If it can handle a list of dicts, we can pass it directly.
            # Assuming for now that the next node expects a string, so we'll format it.
            formatted_content = ""
            for sub_section in sub_sections:
                formatted_content += f"### {sub_section.get('title', 'Untitled Sub-section')}\n"
                formatted_content += f"{sub_section.get('content', '')}\n\n"

            references = [] # References are no longer generated by the extractor
 
            # Update the state with the extracted content and references
            return {
                "current_section_content": formatted_content, # Now contains formatted sub-sections
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
