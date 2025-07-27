from crewai import Agent, Task, Crew, Process
from tools import scrape_website, find_company_website, extract_data
from langchain_openai import ChatOpenAI
import os
from langchain_core.prompts import ChatPromptTemplate
import litellm
from langchain_core.language_models.llms import BaseLLM

# Custom LLM wrapper for Ollama using litellm
class CustomOllama(BaseLLM):
    model: str = "ollama/tinyllama"  # Use smaller, faster model
    base_url: str = "http://localhost:11434"
    temperature: float = 0.1
    timeout: float = 1200.0  # 20 minutes

    def _generate(self, prompts, stop=None, **kwargs):
        print(f"Processing prompt with length: {len(str(prompts))} characters")
        if isinstance(prompts, str):
            messages = [{"role": "user", "content": prompts}]
        else:
            messages = prompts
        for msg in messages:
            if "tool_calls" in msg:
                del msg["tool_calls"]
        response = litellm.completion(
            model=self.model,
            api_base=self.base_url,
            messages=messages,
            temperature=self.temperature,
            max_tokens=1000,  # Reduced for faster processing
            timeout=self.timeout
        )
        from langchain_core.outputs import LLMResult, Generation
        return LLMResult(generations=[[Generation(text=response.choices[0].message.content)]])

    async def _agenerate(self, prompts, stop=None, **kwargs):
        print(f"Processing async prompt with length: {len(str(prompts))} characters")
        if isinstance(prompts, str):
            messages = [{"role": "user", "content": prompts}]
        else:
            messages = prompts
        for msg in messages:
            if "tool_calls" in msg:
                del msg["tool_calls"]
        response = await litellm.acompletion(
            model=self.model,
            api_base=self.base_url,
            messages=messages,
            temperature=self.temperature,
            max_tokens=1000,
            timeout=self.timeout
        )
        from langchain_core.outputs import LLMResult, Generation
        return LLMResult(generations=[[Generation(text=response.choices[0].message.content)]])

    @property
    def _llm_type(self):
        return "custom_ollama"

def get_llm():
    """Get the appropriate LLM based on available options"""
    # Try Grok (xAI) first
    if os.getenv('XAI_API_KEY'):
        print("Using xAI Grok")
        return ChatOpenAI(
            model_name="grok",
            base_url="https://api.x.ai/v1",
            api_key=os.getenv('XAI_API_KEY'),
            temperature=0.1,
            max_tokens=2000
        )
    
    # Try OpenAI if available
    if os.getenv('OPENAI_API_KEY'):
        print("Using OpenAI gpt-3.5-turbo")
        return ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.1,
            max_tokens=2000
        )
    
    # Fallback to Ollama with TinyLlama
    try:
        print("Using Ollama tinyllama")
        os.environ["OLLAMA_API_BASE"] = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
        return CustomOllama()
    except Exception as e:
        print(f"Ollama initialization failed: {str(e)}")
        raise Exception("Ollama server is not running or model 'tinyllama' is not available. Run 'ollama pull tinyllama' or provide a valid xAI/OpenAI API key.")

# Create Agent instances
def create_agent(role, goal, backstory, tools):
    llm = get_llm()
    # Enable tools only for xAI/OpenAI, as Ollama doesn't support tool calls
    use_tools = tools if os.getenv('XAI_API_KEY') or os.getenv('OPENAI_API_KEY') else []
    return Agent(
        role=role,
        goal=goal,
        backstory=backstory,
        verbose=True,
        allow_delegation=False,
        tools=use_tools,
        llm=llm,
        max_iter=3,
        memory=True
    )

WebResearcher = create_agent(
    role='Web Research Specialist',
    goal='Conduct comprehensive web research to gather accurate and up-to-date information about companies, products, and market trends',
    backstory="""You are an expert web researcher with years of experience in market analysis 
    and competitive intelligence. You have a keen eye for finding reliable sources and can 
    distinguish between credible and unreliable information. You excel at finding recent news, 
    company information, and market data from various online sources.""",
    tools=[scrape_website, find_company_website]
)

DataExtractor = create_agent(
    role='Data Extraction Specialist',
    goal='Extract and structure relevant information from company websites and online sources',
    backstory="""You are a skilled data extraction specialist with expertise in web scraping 
    and data parsing. You can efficiently navigate websites, extract key information, and 
    organize it in a structured format. You have experience with various website structures 
    and can adapt to different layouts and formats.""",
    tools=[scrape_website, extract_data]
)

ReportEditor = create_agent(
    role='Research Report Editor',
    goal='Create comprehensive, well-structured reports by synthesizing research data and extracted information',
    backstory="""You are an experienced business analyst and report writer with expertise 
    in creating professional research reports. You excel at synthesizing information from 
    multiple sources, identifying key insights, and presenting findings in a clear, 
    structured format. You have a strong background in business analysis and market research.""",
    tools=[extract_data]
)

MarketAnalyst = create_agent(
    role='Market Analysis Specialist',
    goal='Analyze market trends, competitive landscape, and provide strategic insights',
    backstory="""You are a senior market analyst with deep expertise in competitive 
    intelligence and market research. You can identify market trends, analyze competitive 
    positioning, and provide strategic insights. You have experience across various 
    industries and can quickly understand market dynamics.""",
    tools=[scrape_website, find_company_website]
)

NewsAnalyst = create_agent(
    role='News Analysis Specialist',
    goal='Analyze recent news and developments to provide insights on company performance and public sentiment',
    backstory="""You are a skilled news analyst with expertise in media monitoring and 
    sentiment analysis. You can quickly identify important news developments, analyze 
    their potential impact, and gauge public sentiment. You have experience in financial 
    news analysis and can distinguish between significant and routine news.""",
    tools=[scrape_website, find_company_website]
)

# Task creation functions
def create_research_tasks(company_name):
    """Create tasks for comprehensive company research"""
    
    web_research_task = Task(
        description=f"""
        Conduct comprehensive web research for {company_name}:
        1. Find the official website using the company website finder tool
        2. Research company background, history, and mission
        3. Identify key products and services
        4. Look for recent news and developments
        5. Gather market position information
        
        Company to research: {company_name}
        """,
        agent=WebResearcher,
        expected_output="Comprehensive company information including website, background, products, and recent developments"
    )
    
    data_extraction_task = Task(
        description=f"""
        Extract structured data from {company_name}'s website and online presence:
        1. Scrape the main website content
        2. Extract contact information using the data extraction tool
        3. Extract product/service information
        4. Extract company overview and about information
        5. Organize all extracted data in a structured format
        
        Use the previous research to identify the correct website to scrape.
        """,
        agent=DataExtractor,
        expected_output="Structured data including contact info, products, services, and company details"
    )
    
    market_analysis_task = Task(
        description=f"""
        Analyze {company_name}'s market position and competitive landscape:
        1. Research competitors and market positioning
        2. Analyze industry trends relevant to the company
        3. Identify market opportunities and challenges
        4. Assess company's competitive advantages
        
        Use web research tools to gather competitive intelligence.
        """,
        agent=MarketAnalyst,
        expected_output="Market analysis including competitive landscape, positioning, and industry trends"
    )
    
    news_analysis_task = Task(
        description=f"""
        Analyze recent news and developments about {company_name}:
        1. Find recent news articles and press releases
        2. Analyze sentiment and public perception
        3. Identify significant developments or changes
        4. Assess potential impact on business
        
        Focus on news from the last 6 months.
        """,
        agent=NewsAnalyst,
        expected_output="News analysis including recent developments, sentiment, and impact assessment"
    )
    
    report_creation_task = Task(
        description=f"""
        Create a concise research report for {company_name} using gathered information:
        1. Brief executive summary with key findings
        2. Company overview (100-150 words)
        3. Key products and services (list main offerings)
        4. Basic market position (1-2 sentences)
        5. Recent developments (1-2 sentences)
        6. Contact information (if available)
        
        Keep the report short and focused to minimize processing time.
        """,
        agent=ReportEditor,
        expected_output="A concise research report with summary, overview, products, market position, and recent developments"
    )
    
    return [web_research_task, data_extraction_task, market_analysis_task, news_analysis_task, report_creation_task]

def create_basic_research_tasks(company_name):
    """Create basic research tasks using core agents only"""
    
    research_task = Task(
        description=f"""
        Research {company_name} comprehensively:
        1. Find the official website
        2. Gather company background information
        3. Identify products and services
        4. Look for contact information
        """,
        agent=WebResearcher,
        expected_output="Company research including website, background, and basic information"
    )
    
    extraction_task = Task(
        description=f"""
        Extract structured data from {company_name}:
        1. Scrape website content
        2. Extract contact information
        3. Extract product/service details
        4. Organize information systematically
        """,
        agent=DataExtractor,
        expected_output="Structured company data with contact info and product details"
    )
    
    report_task = Task(
        description=f"""
        Create a concise research report for {company_name}:
        1. Brief executive summary
        2. Company overview (100-150 words)
        3. Key products and services (list main offerings)
        4. Contact information (if available)
        
        Keep the report short to minimize processing time.
        """,
        agent=ReportEditor,
        expected_output="Concise research report with summary, overview, products, and contact info"
    )
    
    return [research_task, extraction_task, report_task]

# Crew creation and execution functions
def run_comprehensive_research(company_name):
    """Run comprehensive research with all agents"""
    
    tasks = create_research_tasks(company_name)
    
    crew = Crew(
        agents=[WebResearcher, DataExtractor, MarketAnalyst, NewsAnalyst, ReportEditor],
        tasks=tasks,
        process=Process.sequential,
        verbose=True
    )
    
    result = crew.kickoff()
    return result

def run_basic_research(company_name):
    """Run basic research with core agents only"""
    
    tasks = create_basic_research_tasks(company_name)
    
    crew = Crew(
        agents=[WebResearcher, DataExtractor, ReportEditor],
        tasks=tasks,
        process=Process.sequential,
        verbose=True
    )
    
    result = crew.kickoff()
    return result

# Helper function for Streamlit integration
def get_available_agents():
    """Return list of available agents for UI"""
    return {
        'WebResearcher': WebResearcher,
        'DataExtractor': DataExtractor,
        'ReportEditor': ReportEditor,
        'MarketAnalyst': MarketAnalyst,
        'NewsAnalyst': NewsAnalyst
    }