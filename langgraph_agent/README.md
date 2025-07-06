# Portfolio Analysis Agent

This project implements a LangGraph-based AI agent designed to analyze portfolio company documents, extract structured data, and iteratively refine the analysis through a review and rewrite process.

## Directory Structure

- `src/`: Contains the core source code of the agent.
    - `agents/`: Defines different agent types or roles (Extractor, Reviewer, Writer).
    - `tools/`: Implements custom tools or functions the agents can use (e.g., `document_loader.py`).
    - `graphs/`: Defines the LangGraph state machines and graph logic (`main_graph.py`).
    - `state.py`: Defines the `AgentState` for the LangGraph workflow.
    - `config/`: Stores configuration files (e.g., API keys, model settings).
- `tests/`: Contains unit and integration tests for the agent components.
- `data/`: Stores any data files used by the agent (e.g., input documents).
- `docs/`: Contains documentation for the project (e.g., `prd.md`).
- `run_agent.py`: The main entry point for running the portfolio analysis agent.
- `pyproject.toml`: Project dependencies and metadata.

## Setup and Running

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd portfolio_analysis/langgraph_agent
    ```

2.  **Install dependencies using Poetry:**
    If you don't have Poetry installed, follow the instructions on their official website: [https://python-poetry.org/docs/#installation](https://python-poetry.org/docs/#installation)
    ```bash
    poetry install
    ```

3.  **Configure Environment Variables:**
    Create a `.env` file in the `langgraph_agent/` directory and add your Google API Key:
    ```
    GOOGLE_API_KEY="your_google_api_key_here"
    ```

4.  **Place your documents:**
    Put the portfolio company documents (PDFs, CSVs, etc.) you want to analyze into the `langgraph_agent/data/` folder. The `run_agent.py` script will create sample files if the folder is empty.

5.  **Run the agent:**
    ```bash
    poetry run python run_agent.py
    ```

    The agent will process the documents, generate an analysis, and save the final report as `portfolio_analysis_report.json` in the `langgraph_agent/` directory.

## Project Structure Overview

The agent's workflow is defined in `src/graphs/main_graph.py` and consists of the following nodes:
- **ExtractorNode**: Performs initial information extraction for a section.
- **ReviewerNode**: Critiques the extracted content and suggests improvements and search terms.
- **WriterNode**: Rewrites the section based on the critique and new information from targeted searches.

The process iterates for each defined section, with a maximum of 3 review loops to refine the content.
</content>