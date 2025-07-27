import streamlit as st
import os
from dotenv import load_dotenv
from agents import WebResearcher, DataExtractor, ReportEditor, run_basic_research, run_comprehensive_research
from tools import scrape_website, find_company_website, extract_data
import requests
import json

# Load environment variables
load_dotenv()

def main():
    st.set_page_config(
        page_title="CrewAI Research Assistant",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 CrewAI Research Assistant")
    st.markdown("---")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        
        # LLM Configuration
        st.subheader("LLM Settings")
        xai_key = st.text_input("xAI API Key (for Grok)", type="password", value=os.getenv('XAI_API_KEY', ''))
        openai_key = st.text_input("OpenAI API Key", type="password", value=os.getenv('OPENAI_API_KEY', ''))
        if xai_key:
            os.environ['XAI_API_KEY'] = xai_key
            st.success("xAI API Key set! Using Grok for faster processing.")
        elif openai_key:
            os.environ['OPENAI_API_KEY'] = openai_key
            st.success("OpenAI API Key set!")
        else:
            st.info("Using Ollama (local LLM) with TinyLlama - ensure it's running with 'ollama run tinyllama'. Note: Local models may be slow on underpowered hardware.")
            try:
                response = requests.get(os.getenv("OLLAMA_API_BASE", "http://localhost:11434") + "/api/tags")
                if response.status_code == 200:
                    models = json.loads(response.text).get("models", [])
                    if any(model["name"] == "tinyllama:latest" for model in models):
                        st.success("Ollama server detected with tinyllama:latest model!")
                    else:
                        st.warning("Ollama server is running, but 'tinyllama:latest' model is not available. Run 'ollama pull tinyllama'.")
                else:
                    st.warning("Ollama server is not responding. Start it with 'ollama run tinyllama'.")
            except requests.exceptions.RequestException:
                st.warning("Ollama server is not running. Start it with 'ollama run tinyllama'.")
        
        # Research Type Selection
        st.subheader("Research Type")
        research_type = st.selectbox(
            "Select research depth:",
            ["Basic Research", "Comprehensive Research"],
            help="Basic: Core information only (faster). Comprehensive: Full analysis including market and news (slower)."
        )
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("Company Research")
        
        # Input form
        with st.form("research_form"):
            company_name = st.text_input(
                "Company Name", 
                placeholder="Enter company name (e.g., 'Tesla', 'Apple Inc.', 'Microsoft')"
            )
            
            submitted = st.form_submit_button("🚀 Start Research", use_container_width=True)
            
            if submitted and company_name:
                with st.spinner(f"Researching {company_name}..."):
                    try:
                        # Run research based on selected type
                        if research_type == "Basic Research":
                            result = run_basic_research(company_name)
                        else:
                            result = run_comprehensive_research(company_name)
                        
                        # Display results
                        st.success("Research completed!")
                        st.subheader("Research Results")
                        
                        # Show the result
                        if isinstance(result, str):
                            st.markdown(result)
                        else:
                            st.write(result)
                            
                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")
                        if "litellm.APIConnectionError" in str(e) and "Timeout" in str(e):
                            st.info("LLM request timed out. Try using 'Basic Research', provide an xAI/OpenAI API key for faster processing, or use a smaller model like 'tinyllama' ('ollama pull tinyllama'). Check your hardware (CPU/GPU, RAM).")
                        elif "litellm.BadRequestError" in str(e):
                            st.info("Failed to initialize LLM. Ensure Ollama is running with 'ollama run tinyllama' or provide a valid xAI/OpenAI API key.")
                        elif "Ollama" in str(e):
                            st.info("Ollama server issue. Ensure it's running with 'ollama run tinyllama' or provide a valid xAI/OpenAI API key.")
                        else:
                            st.info("Please check your API keys, ensure Ollama is running, or verify the company name.")
            
            elif submitted and not company_name:
                st.warning("Please enter a company name.")
    
    with col2:
        st.header("Available Tools")
        
        # Display available tools
        st.subheader("🔧 Research Tools")
        
        tools_info = {
            "Website Scraper": "Scrapes content from company websites (xAI/OpenAI only)",
            "Company Finder": "Finds official company websites (xAI/OpenAI only)",
            "Data Extractor": "Extracts structured data from content (xAI/OpenAI only)"
        }
        
        for tool_name, description in tools_info.items():
            with st.expander(f"🛠️ {tool_name}"):
                st.write(description)
        
        # Display agent information
        st.subheader("🤖 Research Agents")
        
        agents_info = {
            "Web Researcher": "Conducts comprehensive web research",
            "Data Extractor": "Extracts and structures information",
            "Report Editor": "Creates professional reports"
        }
        
        if research_type == "Comprehensive Research":
            agents_info.update({
                "Market Analyst": "Analyzes market position and competition",
                "News Analyst": "Analyzes recent news and sentiment"
            })
        
        for agent_name, description in agents_info.items():
            with st.expander(f"🤖 {agent_name}"):
                st.write(description)
    
    # Footer
    st.markdown("---")
    st.markdown("Built with CrewAI, Streamlit, and xAI/OpenAI/Ollama")

if __name__ == "__main__":
    main()