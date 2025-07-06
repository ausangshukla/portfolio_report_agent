from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.messages import BaseMessage
from ..state import AgentState # Assuming AgentState is in src/state.py

class WriterNode:
    """
    The WriterNode is responsible for rewriting a section based on the critique
    from the ReviewerNode. It uses suggested search terms to find more information
    in the documents and generates an improved version of the section.
    """
    def __init__(self, llm):
        """
        Initializes the WriterNode with a language model.

        Args:
            llm: An instance of a LangChain-compatible language model.
        """
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert financial report writer. Your task is to
             rewrite the provided section of a portfolio analysis report based on the
             given critique and any new information found from targeted searches.

             **Critique:**
             {critique}

             **Original Section Content:**
             {original_content}

             **New Information from Targeted Search (if any):**
             {new_information}

             Integrate the new information, address the critique points (expand on, remove/rephrase),
             and produce a significantly improved version of the section.
             Ensure to update references if new information is used.

             Output your response as a JSON object with two keys:
             'content': The rewritten and improved content for the section.
             'references': An updated list of dictionaries, each with 'document' (filename) and 'location' (page/row).
             """),
            ("user", "Section Title: {section_title}\n{section_instruction}")
        ])
        self.parser = JsonOutputParser()
        self.chain = self.prompt | self.llm | self.parser

    def rewrite(self, state: AgentState) -> Dict[str, Any]:
        """
        Rewrites the current section's content based on critique and new information.

        Args:
            state (AgentState): The current state of the agent.

        Returns:
            Dict[str, Any]: A dictionary containing the updated state with the
                            rewritten section content and references.
        """
        current_section_title = state.get("current_section")
        current_section_instruction = state.get("current_section_instruction", "")
        critique = state.get("critique")
        documents = state.get("documents")
        original_content = state.get("current_section_content", "") # Get content from current_section_content
        original_references = state.get("current_section_references", []) # Get references from current_section_references

        if not current_section_title:
            raise ValueError("No current section specified in the agent state.")
        if not critique:
            print(f"WriterNode: No critique available for section '{current_section_title}'. Skipping rewrite.")
            return {
                "messages": state.get("messages", []) + [
                    BaseMessage(content=f"WriterNode: No critique for '{current_section_title}'. Skipping rewrite.", type="info")
                ]
            }

        if not original_content:
            print(f"WriterNode: No original content found for section '{current_section_title}'. Cannot rewrite.")
            return {
                "messages": state.get("messages", []) + [
                    BaseMessage(content=f"WriterNode: No original content for '{current_section_title}'. Cannot rewrite.", type="error")
                ]
            }

        print(f"--- WriterNode: Rewriting section '{current_section_title}' (Loop: {state.get('loop_count')}) ---")

        # Simulate targeted search based on critique's search terms
        # In a real implementation, this would involve a more sophisticated RAG approach
        new_information = self._perform_targeted_search(documents, critique.get("search_terms", []))
        if new_information != "No new information found for search terms.":
            print(f"WriterNode: New information found for '{current_section_title}'.")

        try:
            rewrite_input = {
                "section_title": current_section_title,
                "critique": critique,
                "original_content": original_content,
                "new_information": new_information,
                "section_instruction": current_section_instruction
            }
            rewrite_result = self.chain.invoke(rewrite_input)

            # Ensure the output matches the expected JSON structure
            rewritten_content = rewrite_result.get("content", "")
            updated_references = rewrite_result.get("references", [])

            # Update the specific section in completed_sections
            # Update the state, including incrementing loop_count
            return {
                "current_section_content": rewritten_content, # Update current_section_content
                "current_section_references": updated_references, # Store references separately
                "loop_count": state.get("loop_count", 0) + 1, # Increment loop_count here
                "messages": state.get("messages", []) + [
                    BaseMessage(content=f"WriterNode: Section '{current_section_title}' rewritten.", type="tool_output")
                ]
            }
        except Exception as e:
            error_message = f"WriterNode: Error during rewrite for '{current_section_title}': {e}"
            print(error_message)
            return {
                "messages": state.get("messages", []) + [
                    BaseMessage(content=error_message, type="error")
                ]
            }

    def _perform_targeted_search(self, documents: List[Dict[str, Any]], search_terms: List[str]) -> str:
        """
        Simulates a targeted search within documents based on search terms.
        In a real application, this would be a sophisticated RAG operation.
        """
        if not search_terms:
            return "No specific search terms provided."

        found_info = []
        for term in search_terms:
            for doc in documents:
                content = doc.get("content", "")
                filename = doc.get("filename", "Unknown")
                # Simple keyword search for demonstration
                if term.lower() in content.lower():
                    # In a real scenario, you'd extract relevant snippets, not whole content
                    found_info.append(f"Found '{term}' in {filename}:\n{content[:200]}...") # Snippet
        return "\n".join(found_info) if found_info else "No new information found for search terms."


if __name__ == "__main__":
    from langchain_community.llms import FakeListLLM
    from ..state import AgentState

    # Mock LLM for testing
    mock_llm = FakeListLLM(responses=[
        '{"content": "This is the improved overview, incorporating market trends from doc3.", "references": [{"document": "doc1.txt", "location": "page 1"}, {"document": "doc3.txt", "location": "page 10"}]}'
    ])

    writer = WriterNode(llm=mock_llm)

    # Mock initial state with a completed section and a critique
    initial_state: AgentState = {
        "documents": [
            {"filename": "doc1.txt", "content": "Company overview: This is a test document for company A."},
            {"filename": "doc3.txt", "content": "Market trends: The market is growing rapidly in 2024."}
        ],
        "sections_to_process": [],
        "completed_sections": [
            {
                "section": "Overview",
                "content": "This is a basic overview of the company. The company is good.",
                "references": [{"document": "doc1.txt", "location": "page 1"}]
            }
        ],
        "current_section": "Overview",
        "loop_count": 0,
        "critique": {
            "expand_on": ["more details on market trends"],
            "remove_or_rephrase": ["The company is good."],
            "search_terms": ["market trends 2024", "industry outlook"]
        },
        "messages": []
    }

    print("\n--- Running WriterNode for 'Overview' ---")
    updated_state = writer.rewrite(initial_state)
    print("Updated State:")
    print(updated_state["completed_sections"])
    print(updated_state["messages"])

    # Simulate no critique
    initial_state_no_critique: AgentState = {
        "documents": [],
        "sections_to_process": [],
        "completed_sections": [
            {
                "section": "Overview",
                "content": "This is a basic overview.",
                "references": []
            }
        ],
        "current_section": "Overview",
        "loop_count": 0,
                "critique": None, # No critique
        "messages": []
    }
    print("\n--- Running WriterNode with no critique ---")
    updated_state_no_critique = writer.rewrite(initial_state_no_critique)
    print("Updated State:")
    print(updated_state_no_critique["messages"])