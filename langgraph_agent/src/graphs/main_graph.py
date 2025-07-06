from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage # Added SystemMessage for context caching
from langchain_google_genai import ChatGoogleGenerativeAI # Using Gemini
from ..state import AgentState
from ..agents.extractor import ExtractorNode
from ..agents.table_generator import TableGeneratorNode
from ..agents.graph_generator import GraphGeneratorNode
from ..agents.reviewer import ReviewerNode
from ..agents.writer import WriterNode
from ..tools.document_loader import load_documents_from_folder

class PortfolioAnalysisGraph:
    """
    Defines the LangGraph state machine for the portfolio analysis agent.
    Orchestrates the Extractor, Reviewer, and Writer nodes in an iterative loop.
    """
    def __init__(self, max_review_loops: int = 1):
        """
        Initializes the PortfolioAnalysisGraph with configuration.
        The LLM will be initialized within run_analysis to support context caching.

        Args:
            max_review_loops (int): The maximum number of times a section can be reviewed and rewritten.
        """
        self.max_review_loops = max_review_loops
        # Nodes will be initialized in run_analysis with the cached LLM
        self.extractor_node = None
        self.reviewer_node = None
        self.writer_node = None
        self.table_generator_node = None
        self.graph_generator_node = None
        self.graph = None # Graph will be built after LLM is ready

    def _build_graph(self):
        """
        Builds the LangGraph state machine. This method is now called
        within run_analysis after the LLM and nodes are initialized.
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
        # "table_generator": Generates tabular data for the section.
        workflow.add_node("table_generator", self.table_generator_node.generate_table)
        # "graph_generator": Generates graph specifications for the section.
        workflow.add_node("graph_generator", self.graph_generator_node.generate_graph)

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
                # If the decider returns "table_generation", transition to the "table_generator" node.
                "table_generation": "table_generator"
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
                # If the decider returns "table_generation", transition to the "table_generator" node.
                "table_generation": "table_generator"
            }
        )

        # After the "writer" node runs, transition to the "table_generator" node.
        workflow.add_edge("writer", "table_generator")

        # After the "table_generator" node runs, transition to the "graph_generator" node.
        workflow.add_edge("table_generator", "graph_generator")

        # After the "graph_generator" node runs, the current section's processing ends (END).
        workflow.add_edge("graph_generator", END)

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
        return "review" # Always go to review after extraction

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
            print(f"Decider: No actionable critique or max loops reached for '{state.get('current_section')}' ({loop_count}/{self.max_review_loops}). Proceeding to table generation.")
            return "table_generation"

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

        # After writing, if there's still a need for review (e.g., max loops not reached), go back to reviewer.
        # Otherwise, proceed to table generation.
        if loop_count < self.max_review_loops:
            print(f"Decider: Loops remaining for '{state.get('current_section')}' ({loop_count}/{self.max_review_loops}). Proceeding to re-review.")
            return "review"
        else:
            print(f"Decider: Max loops reached for '{state.get('current_section')}' ({loop_count}/{self.max_review_loops}). Proceeding to table generation.")
            return "table_generation" # New transition to table generation

    def run_analysis(self, llm: Any, loaded_docs: List[Dict[str, Any]], sections: List[Dict[str, str]]):
        """
        Executes the entire portfolio analysis process using the defined LangGraph.
        It initializes the agent state with pre-loaded documents, and then iteratively processes
        each specified section through the Extractor, Reviewer, and Writer nodes.

        Args:
            loaded_docs (List[Dict[str, Any]]): A list of pre-loaded documents, each with 'filename', 'content', and 'metadata'.
            sections (List[Dict[str, str]]): A list of dictionaries, where each dictionary contains
                                            'title' (the section title) and 'instruction' (additional LLM instruction).

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, where each dictionary represents
                                  a fully processed and refined section of the analysis.
                                  Each section includes its content and references.
        """
        if not loaded_docs:
            print("No documents provided. Exiting analysis.")
            return []

        # Initialize agent nodes with the provided LLM
        self.extractor_node = ExtractorNode(llm)
        self.reviewer_node = ReviewerNode(llm)
        self.writer_node = WriterNode(llm)
        self.table_generator_node = TableGeneratorNode(llm)
        self.graph_generator_node = GraphGeneratorNode(llm)
        
        # Build the graph now that nodes are initialized
        self.graph = self._build_graph()
        print("--- LangGraph built with cached LLM ---")

        # Initialize the overall state for the agent.
        initial_state: AgentState = {
            "documents": loaded_docs, # All loaded documents available to all nodes.
            "sections_to_process": sections, # List of sections to iterate through.
            "completed_sections": [], # Accumulates the final versions of processed sections.
            "current_section": None, # The section title currently being worked on by the graph.
            "current_section_instruction": None, # The instruction for the current section.
            "loop_count": 0, # Tracks review iterations for the current section.
            "critique": None, # Stores feedback from the reviewer for the writer.
            "tabular_data": None, # Stores generated tabular data for the current section.
            "graph_specs": [], # Stores generated graph specifications for the current section (now a list).
            "messages": [BaseMessage(content="Analysis started.", type="info")] # Log of agent's actions.
        }

        # Iterate through each section defined in `sections_to_analyze`.
        for section_info in sections:
            section_title = section_info["title"]
            section_instruction = section_info["instruction"]
            print(f"\n--- Starting analysis for section: '{section_title}' with instruction: '{section_instruction}' ---")
            # Create a copy of the initial state for the current section's processing.
            current_section_state = initial_state.copy()
            current_section_state["current_section"] = section_title
            current_section_state["current_section_instruction"] = section_instruction
            current_section_state["critique"] = None # Reset critique for each new section.
            current_section_state["loop_count"] = 0 # Reset loop count for each new section.

            # Run the graph for the current section
            final_state_after_stream = None
            for i, s in enumerate(self.graph.stream(current_section_state)):
                # LangGraph stream yields a dictionary where the key is the node name
                # and the value is the state update from that node.
                # We need to unwrap this to get the actual state update.
                node_output = list(s.values())[0]
                current_section_state.update(node_output)
                final_state_after_stream = current_section_state # Keep track of the final state
                print(f"--- Debug: State after stream step {i} for '{section_title}': {current_section_state} ---")

            print(f"--- Debug: Final state after stream for '{section_title}': {final_state_after_stream} ---")

            # After the graph for a single section completes (reaches END),
            # consolidate all relevant data for the current section and add it to completed_sections.
            finalized_section = {
                "section": section_title,
                "instruction": section_instruction, # Include the instruction in the finalized report
                "content": final_state_after_stream.get("current_section_content", ""),
                "references": final_state_after_stream.get("current_section_references", []),
                "tabular_data": final_state_after_stream.get("tabular_data", None),
                "graph_specs": final_state_after_stream.get("graph_specs", []) # Changed to graph_specs (plural)
            }
            
            print(f"--- Finalized section '{section_title}' ---")
            yield finalized_section
            
            # Update the overall `initial_state` with the finalized section.
            # This is crucial for subsequent sections to have access to previously
            # completed sections if needed for context.
            initial_state["completed_sections"].append(finalized_section)

        print("\n--- Portfolio Analysis Completed ---")

