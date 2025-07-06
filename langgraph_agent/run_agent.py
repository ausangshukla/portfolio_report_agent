import os
import json
import datetime
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI # Example LLM
from src.graphs.main_graph import PortfolioAnalysisGraph
from src.tools.document_loader import load_documents_from_folder
from src.utils.report_generator import generate_word_report

def main():
    """
    Main function to run the portfolio analysis agent.
    """
    # Load environment variables from .env file
    load_dotenv()

    # Configure your LLM
    # Ensure GOOGLE_API_KEY is set in your .env file or environment
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("Error: GOOGLE_API_KEY not found in environment variables.")
        print("Please set it in a .env file or directly in your environment.")
        return

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-preview-05-20", google_api_key=google_api_key)

    # Define the path to your portfolio documents
    # For demonstration, we'll use a dummy folder.
    # In a real scenario, this would be your actual data folder.
    data_folder = "langgraph_agent/data" # Assuming data folder is within langgraph_agent

    # Create a dummy data folder and some files for testing if they don't exist
    os.makedirs(data_folder, exist_ok=True)
    # if not os.path.exists(os.path.join(data_folder, "sample_report.txt")):
    #     with open(os.path.join(data_folder, "sample_report.txt"), "w") as f:
    #         f.write("This is a sample annual report for Company X. Revenue was $100M in 2023. Profit was $20M. Key risks include market volatility. Strategic insights: focus on innovation.")
    # if not os.path.exists(os.path.join(data_folder, "sample_kpis.csv")):
    #     with open(os.path.join(data_folder, "sample_kpis.csv"), "w") as f:
    #         f.write("KPI,Value\nRevenue,100M\nProfit,20M\nCustomers,500K")

    # Define the sections to analyze
    sections_to_analyze = [
        "Overview",
        # "Financial Review",
        # "Risks",
        # "Strategic Insights",
        # "Competition" # This section might not have direct content in sample, testing robustness
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
            if not first_section:
                f.write(",\n") # Add comma for subsequent sections
            
            json.dump(section_report, f, indent=2)
            first_section = False
            
        f.write("\n]\n") # End JSON array
        
    print(f"\nPortfolio analysis completed. Report saved to '{output_file}'")

    # Generate Word document from the JSON report
    word_output_file = os.path.join(output_dir, f"portfolio_analysis_report_{timestamp}.docx")
    generate_word_report(output_file, word_output_file)

    # Clean up dummy data after execution
    if os.path.exists(os.path.join(data_folder, "sample_report.txt")):
        os.remove(os.path.join(data_folder, "sample_report.txt"))
    if os.path.exists(os.path.join(data_folder, "sample_kpis.csv")):
        os.remove(os.path.join(data_folder, "sample_kpis.csv"))
    # os.rmdir(data_folder) # Only remove if empty, otherwise it will fail

if __name__ == "__main__":
    main()