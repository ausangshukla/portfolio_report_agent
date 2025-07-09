import os
import json
import datetime
import sys # Import sys to access command-line arguments
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI # Example LLM
from src.graphs.main_graph import PortfolioAnalysisGraph
from src.tools.document_loader import load_documents_from_folder
from src.utils.report_generator import generate_html_report

def main():
    """
    Main function to run the portfolio analysis agent.
    It now accepts a folder name as a command-line argument to specify
    which data folder to load documents from.
    """
    # Check for command-line arguments
    if len(sys.argv) < 2:
        print("Usage: poetry run python run_agent.py <folder_name>")
        print("Please provide the name of the folder within 'langgraph_agent/data' to analyze.")
        return
    
    folder_name = sys.argv[1]

    # Load environment variables from .env file
    load_dotenv()

    # Configure your LLM
    # Ensure GOOGLE_API_KEY is set in your .env file or environment
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("Error: GOOGLE_API_KEY not found in environment variables.")
        print("Please set it in a .env file or directly in your environment.")
        return

    # gemini-2.5-pro-preview-06-05
    # gemini-2.5-flash-preview-05-20
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-preview-05-20", google_api_key=google_api_key)

    # Define the path to your portfolio documents
    # Construct the path to your portfolio documents using the provided folder name
    base_data_path = "langgraph_agent/data"
    data_folder = os.path.join(base_data_path, folder_name)

    # Ensure the specified data folder exists
    if not os.path.exists(data_folder):
        print(f"Error: Data folder '{data_folder}' not found.")
        print("Please ensure the folder exists within 'langgraph_agent/data'.")
        return

    # The following lines for creating dummy files are commented out as they are not needed
    # if not os.path.exists(os.path.join(data_folder, "sample_report.txt")):
    #     with open(os.path.join(data_folder, "sample_report.txt"), "w") as f:
    #         f.write("This is a sample annual report for Company X. Revenue was $100M in 2023. Profit was $20M. Key risks include market volatility. Strategic insights: focus on innovation.")
    # if not os.path.exists(os.path.join(data_folder, "sample_kpis.csv")):
    #     with open(os.path.join(data_folder, "sample_kpis.csv"), "w") as f:
    #         f.write("KPI,Value\nRevenue,100M\nProfit,20M\nCustomers,500K")

    # Define the sections to analyze
    # Each section can now have a title and an instruction for the LLM, separated by a colon.
    # The part before the colon is the section title, and the part after is the instruction.
    sections_to_analyze = [
        {
            "name": "Executive Summary",
            "section_instructions": "Highlight the key investment thesis for the company and summarize the main financial and operating metrics. Keep it terse and focused with sub_sections being 2-3 lines only",
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

    # Initialize and run the graph
    print("Initializing Portfolio Analysis Agent...")
    agent_graph = PortfolioAnalysisGraph(max_review_loops=1) # Max 3 review loops per section

    print("Starting portfolio analysis...")
    print(f"Data folder for analysis: {data_folder}")
    
    # Load documents and print the list of loaded documents
    loaded_docs = load_documents_from_folder(data_folder)
    if not loaded_docs:
        print("No documents found in the data folder. Exiting.")
        return
    
    print("Documents identified for processing:")
    for doc in loaded_docs:
        print(f"- {doc['filename']} (Type: {doc['metadata'].get('type', 'unknown')})")

    # Pass the loaded documents directly to the graph's run_analysis method
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"portfolio_analysis_report_{timestamp}.json")
    
    print(f"Starting portfolio analysis and writing incremental report to '{output_file}'...")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("[\n") # Start JSON array
        
        first_section = True
        for section_report in agent_graph.run_analysis(llm, loaded_docs, sections_to_analyze):
            print(f"--- Debug: Section report yielded to run_agent.py: {section_report} ---")
            if not first_section:
                f.write(",\n") # Add comma for subsequent sections
            
            json.dump(section_report, f, indent=2)
            first_section = False
            
        f.write("\n]\n") # End JSON array
        
    print(f"\nPortfolio analysis completed. Report saved to '{output_file}'")

    # Generate HTML report from the JSON report
    html_output_file = os.path.join(output_dir, f"portfolio_analysis_report_{timestamp}.html")
    generate_html_report(output_file, html_output_file)

   

if __name__ == "__main__":
    main()