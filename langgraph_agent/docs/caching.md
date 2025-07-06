# Plan to Implement Explicit Context Caching

Based on the analysis of `graph_generator.py` and `main_graph.py`, the `documents` passed to the prompt are a large, stable piece of context, making this an ideal scenario for explicit context caching. The `PortfolioAnalysisGraph` class initializes all agent nodes with the same `llm` instance, and the `run_analysis` method takes `loaded_docs` which remains constant. This confirms that explicit caching is the right approach.

## Implementation Steps

1.  **Update Imports:** Add the necessary imports for `create_context_cache` and `timedelta` to `langgraph_agent/src/graphs/main_graph.py`.

2.  **Modify `run_analysis`:** Inside the `run_analysis` method, the following will be done:
    *   A stable context will be created by combining the `loaded_docs` into a single `SystemMessage`.
    *   `create_context_cache` will be called with this message to get a cache handle.
    *   A new, cached `ChatVertexAI` model will be instantiated using this handle.
    *   All agent nodes (`extractor_node`, `reviewer_node`, etc.) will be re-initialized with this new cached `llm` instance.

3.  **Update Node Initialization:** The agent nodes are currently initialized in the `__init__` method. Their initialization will be moved to the `run_analysis` method so they can be created with the cached `llm`.

This approach ensures the large document context is sent to the Gemini API only once per run, dramatically reducing token usage and cost.

## Visual Plan

Here is a Mermaid diagram illustrating the proposed change to the workflow:

```mermaid
graph TD
    subgraph Current Workflow
        A[run_analysis receives llm] --> B[Nodes initialized with llm in __init__];
        B --> C[graph.stream processes data];
    end

    subgraph Proposed Workflow
        A_new[run_analysis receives llm] --> D{Create Context Cache from docs};
        D --> E{Create cached_llm};
        E --> F[Nodes initialized with cached_llm in run_analysis];
        F --> G[graph.stream processes data];
    end

    style B fill:#f9f,stroke:#333,stroke-width:2px
    style F fill:#ccf,stroke:#333,stroke-width:2px