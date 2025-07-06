from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage
from ..state import AgentState
from ..agents.extractor import ExtractorNode
from ..agents.reviewer import ReviewerNode
from ..agents.writer import WriterNode
from ..tools.document_loader import load_documents_from_folder

class PortfolioAnalysisGraph:
    """
    Defines the LangGraph state machine for the portfolio analysis agent.
    Orchestrates the Extractor, Reviewer, and Writer nodes in an iterative loop.
    """
    def __init__(self, llm, max_review_loops: int = 2):
        """
        Initializes the PortfolioAnalysisGraph with a language model and configuration.

        Args:
            llm: An instance of a LangChain-compatible language model.
            max_review_loops (int): The maximum number of times a section can be reviewed and rewritten.
        """
        self.llm = llm
        self.max_review_loops = max_review_loops
        self.extractor_node = ExtractorNode(llm)
        self.reviewer_node = ReviewerNode(llm)
        self.writer_node = WriterNode(llm)
        self.graph = self._build_graph()

    def _build_graph(self):
        """
        Builds the LangGraph state machine.
        """
        # Initialize the StateGraph with the AgentState schema.
        # This defines the structure of the data that will be passed between nodes.
        workflow = StateGraph(AgentState)

        # Add nodes to the graph. Each node represents a step in our agent's workflow.
        # "extractor": Uses the ExtractorNode to perform initial data extraction.
        workflow.add_node("extractor", self.extractor_node.extract)
        # "reviewer": Uses the ReviewerNode to critique the extracted content.
        workflow.add_node("reviewer", self.reviewer_node.review)
        # "writer": Uses the WriterNode to rewrite content based on critique.
        workflow.add_node("writer", self.writer_node.rewrite)

        # Set the starting point of the graph.
        # The workflow will always begin by calling the "extractor" node.
        workflow.set_entry_point("extractor")

        # Define the edges (transitions) between nodes.
        # Conditional edges allow the graph to choose the next node based on the state.

        # After the "extractor" node runs, call the `_decide_next_step_after_extraction` function.
        # This function will return a string ("review" or "next_section") which determines the next node.
        workflow.add_conditional_edges(
            "extractor",
            self._decide_next_step_after_extraction,
            {
                # If the decider returns "review", transition to the "reviewer" node.
                "review": "reviewer",
                # If the decider returns "next_section", the current section's processing ends (END).
                "next_section": END
            }
        )

        # After the "reviewer" node runs, call the `_decide_next_step_after_review` function.
        # This function will return a string ("rewrite" or "next_section").
        workflow.add_conditional_edges(
            "reviewer",
            self._decide_next_step_after_review,
            {
                # If the decider returns "rewrite", transition to the "writer" node.
                "rewrite": "writer",
                # If the decider returns "next_section", the current section's processing ends (END).
                "next_section": END
            }
        )

        # After the "writer" node runs, call the `_decide_next_step_after_writer` function.
        # This function will return a string ("review" or "next_section").
        workflow.add_conditional_edges(
            "writer",
            self._decide_next_step_after_writer,
            {
                # If the decider returns "review", transition back to the "reviewer" node for another loop.
                "review": "reviewer",
                # If the decider returns "next_section", the current section's processing ends (END).
                "next_section": END
            }
        )

        # Compile the workflow into a runnable LangGraph.
        # This prepares the graph for execution.
        return workflow.compile()

    def _decide_next_step_after_extraction(self, state: AgentState) -> str:
        """
        Decider function: Determines the next step after the ExtractorNode has completed its run.
        In this design, after the initial extraction, we always proceed to the ReviewerNode
        to get feedback on the first draft.
        """
        print(f"--- Decider: After ExtractorNode for section '{state.get('current_section')}' ---")
        return "review"

    def _decide_next_step_after_review(self, state: AgentState) -> str:
        """
        Decider function: Determines the next step after the ReviewerNode has provided its critique.
        It checks if there's a valid critique (i.e., something to expand on or rephrase)
        and if the maximum number of review loops for the current section has not been reached.
        If both conditions are met, it transitions to the WriterNode for refinement.
        Otherwise, it signals that the current section is complete and moves to the next section.
        """
        print(f"--- Decider: After ReviewerNode for section '{state.get('current_section')}' ---")
        critique = state.get("critique")
        loop_count = state.get("loop_count", 0)

        if critique and (critique.get("expand_on") or critique.get("remove_or_rephrase")) and loop_count < self.max_review_loops:
            print(f"Decider: Critique present for '{state.get('current_section')}'. Loops remaining ({loop_count}/{self.max_review_loops}). Proceeding to rewrite.")
            return "rewrite"
        else:
            print(f"Decider: No actionable critique or max loops reached for '{state.get('current_section')}' ({loop_count}/{self.max_review_loops}). Moving to next section.")
            return "next_section"

    def _decide_next_step_after_writer(self, state: AgentState) -> str:
        """
        Decider function: Determines the next step after the WriterNode has rewritten a section.
        It increments the `loop_count` for the current section.
        If the `loop_count` is still below the `max_review_loops`, it transitions back to the
        ReviewerNode for another round of critique and refinement.
        Otherwise, it signals that the current section has undergone enough review cycles
        and moves to the next section.
        """
        print(f"--- Decider: After WriterNode for section '{state.get('current_section')}' ---")
        loop_count = state.get("loop_count", 0)

        if loop_count < self.max_review_loops:
            print(f"Decider: Loops remaining for '{state.get('current_section')}' ({loop_count}/{self.max_review_loops}). Proceeding to re-review.")
            return "review"
        else:
            print(f"Decider: Max loops reached for '{state.get('current_section')}' ({loop_count}/{self.max_review_loops}). Moving to next section.")
            return "next_section"

    def run_analysis(self, loaded_docs: List[Dict[str, Any]], sections: List[str]):
        """
        Executes the entire portfolio analysis process using the defined LangGraph.
        It initializes the agent state with pre-loaded documents, and then iteratively processes
        each specified section through the Extractor, Reviewer, and Writer nodes.

        Args:
            loaded_docs (List[Dict[str, Any]]): A list of pre-loaded documents, each with 'filename', 'content', and 'metadata'.
            sections (List[str]): A list of strings, where each string is the title
                                  of a section to be generated in the analysis report
                                  (e.g., "Overview", "Financial Review", "Risks").

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, where each dictionary represents
                                  a fully processed and refined section of the analysis.
                                  Each section includes its content and references.
        """
        # Documents are now pre-loaded and passed directly.
        if not loaded_docs:
            print("No documents provided. Exiting analysis.")
            return []

        # Step 2: Initialize the overall state for the agent.
        # This state will be passed and updated across different nodes in the graph.
        initial_state: AgentState = {
            "documents": loaded_docs, # All loaded documents available to all nodes.
            "sections_to_process": sections, # List of sections to iterate through.
            "completed_sections": [], # Accumulates the final versions of processed sections.
            "current_section": None, # The section currently being worked on by the graph.
            "loop_count": 0, # Tracks review iterations for the current section.
            "critique": None, # Stores feedback from the reviewer for the writer.
            "messages": [BaseMessage(content="Analysis started.", type="info")] # Log of agent's actions.
        }

        # Step 3: Iterate through each section defined in `sections_to_analyze`.
        for section_title in sections:
            print(f"\n--- Starting analysis for section: '{section_title}' ---")
            # Create a copy of the initial state for the current section's processing.
            # This ensures each section starts with a clean loop count and critique.
            current_section_state = initial_state.copy()
            current_section_state["current_section"] = section_title
            current_section_state["critique"] = None # Reset critique for each new section.
            current_section_state["loop_count"] = 0 # Reset loop count for each new section.

            # Run the graph for the current section
            for s in self.graph.stream(current_section_state):
                current_section_state.update(s)

            # After the graph for a single section completes (reaches END),
            # extract the final version of that section from `completed_sections`
            # and yield it.
            found_section = None
            for section_item in current_section_state["completed_sections"]:
                if section_item["section"] == section_title:
                    print(f"--- Finalized section '{section_title}' ---")
                    yield section_item
                    found_section = section_item
                    break
            
            # Update the overall `initial_state` with the finalized section if found.
            # This is crucial for subsequent sections to have access to previously
            # completed sections if needed for context.
            if found_section:
                initial_state["completed_sections"].append(found_section)
            else:
                print(f"Warning: No finalized content found for section '{section_title}'.")


        print("\n--- Portfolio Analysis Completed ---")

