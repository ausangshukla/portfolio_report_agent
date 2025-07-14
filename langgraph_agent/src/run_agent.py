import os
import json
import datetime
import sys # Import sys to access command-line arguments
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI # Example LLM
from src.graphs.main_graph import PortfolioAnalysisGraph
from src.tools.document_loader import load_documents_from_folder
from src.utils.report_generator import generate_html_report

DEFAULT_SECTIONS_TO_ANALYZE = [
    {
        "name": "Executive Summary",
        "section_instructions": "Highlight the key investment thesis for the company and summarize the main financial and operating metrics. Keep it focused with each sub_section being 3-4 lines only",
        "include_table": True,
        "table_instructions": "",
        "include_graphs": True,
        "graph_instructions": ""
    },
    {
        "name": "Overview",
        "section_instructions": "Provide a brief overview of the company, including its history, mission, and key products or services. Also include founder and key management.",
        "include_table": True,
        "table_instructions": "",
        "include_graphs": False,
        "graph_instructions": ""
    },
    {
        "name": "Strategic Insights",
        "section_instructions": "Summarize the strategic insights from the annual report, focusing on the company's long-term vision and strategic initiatives. Do not generate markdown tables, just text",
        "include_table": False,
        "table_instructions": "",
        "include_graphs": True,
        "graph_instructions": ""
    },
    {
        "name": "Financial Review",
        "section_instructions": "Analyze the financial performance of the company, including revenue, profit margins, and key financial ratios. Do not generate markdown tables, just text.",
        "include_table": True,
        "table_instructions": "",
        "include_graphs": True,
        "graph_instructions": ""
    },
    {
        "name": "Risks",
        "section_instructions": "Identify and analyze the key risks facing the company, including market, operational, and financial risks.",
        "include_table": True,
        "table_instructions": "",
        "include_graphs": False,
        "graph_instructions": ""
    }
]

def run_portfolio_analysis(folder_name: str, sections_to_analyze: list = None):
    """
    Runs the portfolio analysis agent for a given data folder and sections.

    Args:
        folder_name (str): The name of the folder within 'langgraph_agent/data' to analyze.
        sections_to_analyze (list, optional): A list of dictionaries defining the sections
                                               to analyze. If None, a default set of sections
                                               will be used.
    """
    load_dotenv()

    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("Error: GOOGLE_API_KEY not found in environment variables.")
        print("Please set it in a .env file or directly in your environment.")
        return

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-preview-05-20", google_api_key=google_api_key)

    data_folder = folder_name

    if not os.path.exists(data_folder):
        print(f"Error: Data folder '{data_folder}' not found.")
        print("Please ensure the folder exists.")
        return

    sections_to_analyze = sections_to_analyze if sections_to_analyze is not None else DEFAULT_SECTIONS_TO_ANALYZE

    print("Initializing Portfolio Analysis Agent...")
    agent_graph = PortfolioAnalysisGraph(max_review_loops=1)

    print("Starting portfolio analysis...")
    print(f"Data folder for analysis: {data_folder}")
    
    loaded_docs = load_documents_from_folder(data_folder)
    if not loaded_docs:
        print("No documents found in the data folder. Exiting.")
        return
    
    print("Documents identified for processing:")
    for doc in loaded_docs:
        print(f"- {doc['filename']} (Type: {doc['metadata'].get('type', 'unknown')})")

    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"portfolio_analysis_report_{timestamp}.json")
    
    print(f"Starting portfolio analysis and writing incremental report to '{output_file}'...")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("[\n")
        
        first_section = True
        for section_report in agent_graph.run_analysis(llm, loaded_docs, sections_to_analyze):
            if not first_section:
                f.write(",\n")
            
            json.dump(section_report, f, indent=2)
            first_section = False
            
        f.write("\n]\n")
        
    print(f"\nPortfolio analysis completed. Report saved to '{output_file}'")

    html_output_file = os.path.join(output_dir, f"portfolio_analysis_report_{timestamp}.html")
    generate_html_report(output_file, html_output_file)

def main():
    """
    Main function to run the portfolio analysis agent.
    It now accepts a folder name as a command-line argument to specify
    which data folder to load documents from.
    """
    if len(sys.argv) < 2:
        print("Usage: poetry run python run_agent.py <path_to_data_folder>")
        print("Please provide the full path to the data folder to analyze.")
        return
    
    folder_name = sys.argv[1]
    run_portfolio_analysis(folder_name)

if __name__ == "__main__":
    main()