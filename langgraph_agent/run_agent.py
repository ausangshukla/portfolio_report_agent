import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI # Example LLM
from src.graphs.main_graph import PortfolioAnalysisGraph
from src.tools.document_loader import load_documents_from_folder

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
    if not os.path.exists(os.path.join(data_folder, "sample_report.txt")):
        with open(os.path.join(data_folder, "sample_report.txt"), "w") as f:
            f.write("This is a sample annual report for Company X. Revenue was $100M in 2023. Profit was $20M. Key risks include market volatility. Strategic insights: focus on innovation.")
    if not os.path.exists(os.path.join(data_folder, "sample_kpis.csv")):
        with open(os.path.join(data_folder, "sample_kpis.csv"), "w") as f:
            f.write("KPI,Value\nRevenue,100M\nProfit,20M\nCustomers,500K")

    # Define the sections to analyze
    sections_to_analyze = [
        "Overview",
        "Financial Review",
        "Risks",
        "Strategic Insights",
        "Competition" # This section might not have direct content in sample, testing robustness
    ]

    # Initialize and run the graph
    print("Initializing Portfolio Analysis Agent...")
    agent_graph = PortfolioAnalysisGraph(llm=llm, max_review_loops=3) # Max 3 review loops per section

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
    # This requires a slight modification to run_analysis to accept loaded_docs
    final_report = agent_graph.run_analysis(loaded_docs, sections_to_analyze)

    # Output the final report
    output_file = "portfolio_analysis_report.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_report, f, indent=2)
    print(f"\nPortfolio analysis completed. Report saved to '{output_file}'")

    # Clean up dummy data after execution
    if os.path.exists(os.path.join(data_folder, "sample_report.txt")):
        os.remove(os.path.join(data_folder, "sample_report.txt"))
    if os.path.exists(os.path.join(data_folder, "sample_kpis.csv")):
        os.remove(os.path.join(data_folder, "sample_kpis.csv"))
    # os.rmdir(data_folder) # Only remove if empty, otherwise it will fail

if __name__ == "__main__":
    main()