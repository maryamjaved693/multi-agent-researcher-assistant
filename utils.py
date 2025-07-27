import os
import json
import re
from typing import Dict, List, Any, Optional
import streamlit as st
from datetime import datetime
import hashlib
import requests
from urllib.parse import urlparse, urljoin
import time

def validate_environment():
    """Validate that all required environment variables are set"""
    
    required_vars = {
        'SERPER_API_KEY': 'Web search functionality',
        'FIRECRAWL_API_KEY': 'Web scraping with Firecrawl (optional if JINA_API_KEY is set)',
        'JINA_API_KEY': 'Web scraping with Jina.ai (optional if FIRECRAWL_API_KEY is set)'
    }
    
    missing_vars = []
    warnings = []
    
    for var, description in required_vars.items():
        if not os.getenv(var):
            if 'optional' in description:
                warnings.append(f"{var}: {description}")
            else:
                missing_vars.append(f"{var}: {description}")
    
    # Check if at least one scraping tool is available
    if not os.getenv('FIRECRAWL_API_KEY') and not os.getenv('JINA_API_KEY'):
        missing_vars.append("Either FIRECRAWL_API_KEY or JINA_API_KEY: Required for web scraping")
    
    return missing_vars, warnings

def setup_environment_ui():
    """Display environment setup UI in Streamlit"""
    
    st.sidebar.header("🔧 Environment Setup")
    
    missing_vars, warnings = validate_environment()
    
    if missing_vars:
        st.sidebar.error("Missing Required Variables:")
        for var in missing_vars:
            st.sidebar.write(f"❌ {var}")
    
    if warnings:
        st.sidebar.warning("Optional Variables:")
        for var in warnings:
            st.sidebar.write(f"⚠️ {var}")
    
    if not missing_vars:
        st.sidebar.success("✅ Environment configured correctly!")
    
    # Environment variable input
    with st.sidebar.expander("Set Environment Variables"):
        st.write("**Set your API keys:**")
        
        serper_key = st.text_input("SERPER_API_KEY", type="password", help="Get free key from serper.dev")
        firecrawl_key = st.text_input("FIRECRAWL_API_KEY", type="password", help="Get free key from firecrawl.dev")
        jina_key = st.text_input("JINA_API_KEY", type="password", help="Get free key from jina.ai")
        
        if st.button("Set Environment Variables"):
            if serper_key:
                os.environ['SERPER_API_KEY'] = serper_key
            if firecrawl_key:
                os.environ['FIRECRAWL_API_KEY'] = firecrawl_key
            if jina_key:
                os.environ['JINA_API_KEY'] = jina_key
            st.success("Environment variables updated!")
            st.rerun()

def format_research_results(results: str) -> Dict[str, Any]:
    """Format research results for better display"""
    
    formatted = {
        'executive_summary': '',
        'company_overview': '',
        'products_services': '',
        'market_position': '',
        'recent_news': '',
        'key_insights': '',
        'raw_data': str(results)
    }
    
    # Split results into sections
    sections = str(results).split('\n\n')
    
    current_section = None
    for section in sections:
        section = section.strip()
        if not section:
            continue
            
        # Identify section type
        section_lower = section.lower()
        
        if any(keyword in section_lower for keyword in ['executive', 'summary']):
            formatted['executive_summary'] = section
        elif any(keyword in section_lower for keyword in ['company', 'overview', 'background']):
            formatted['company_overview'] = section
        elif any(keyword in section_lower for keyword in ['product', 'service', 'offering']):
            formatted['products_services'] = section
        elif any(keyword in section_lower for keyword in ['market', 'position', 'competitor']):
            formatted['market_position'] = section
        elif any(keyword in section_lower for keyword in ['news', 'recent', 'development']):
            formatted['recent_news'] = section
        elif any(keyword in section_lower for keyword in ['insight', 'recommendation', 'conclusion']):
            formatted['key_insights'] = section
    
    return formatted

def generate_report_filename(company_name: str) -> str:
    """Generate a filename for the research report"""
    
    # Clean company name
    clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', company_name)
    clean_name = re.sub(r'\s+', '_', clean_name.strip())
    
    # Add timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    return f"{clean_name}_research_report_{timestamp}.txt"

def cache_results(company_name: str, results: Any) -> str:
    """Cache research results (in-memory for this session)"""
    
    if 'research_cache' not in st.session_state:
        st.session_state.research_cache = {}
    
    cache_key = hashlib.md5(company_name.lower().encode()).hexdigest()
    st.session_state.research_cache[cache_key] = {
        'company_name': company_name,
        'results': results,
        'timestamp': datetime.now().isoformat()
    }
    
    return cache_key

def get_cached_results(company_name: str) -> Optional[Any]:
    """Get cached research results"""
    
    if 'research_cache' not in st.session_state:
        return None
    
    cache_key = hashlib.md5(company_name.lower().encode()).hexdigest()
    cached_data = st.session_state.research_cache.get(cache_key)
    
    if cached_data:
        # Check if cache is still valid (within 1 hour)
        cache_time = datetime.fromisoformat(cached_data['timestamp'])
        if (datetime.now() - cache_time).seconds < 3600:
            return cached_data['results']
    
    return None

def validate_url(url: str) -> bool:
    """Validate if a URL is properly formatted"""
    
    try:
        parsed = urlparse(url)
        return bool(parsed.netloc) and bool(parsed.scheme)
    except:
        return False

def clean_text(text: str) -> str:
    """Clean and format text for better readability"""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s\.\,\!\?\-\(\)]', '', text)
    
    # Fix spacing around punctuation
    text = re.sub(r'\s+([,.!?])', r'\1', text)
    text = re.sub(r'([,.!?])\s*', r'\1 ', text)
    
    return text

def extract_key_metrics(content: str) -> Dict[str, List[str]]:
    """Extract key metrics and data points from content"""
    
    metrics = {
        'financial_data': [],
        'growth_metrics': [],
        'market_share': [],
        'employee_count': [],
        'founding_info': []
    }
    
    # Financial data patterns
    financial_patterns = [
        r'\$[\d,]+\.?\d*[BMK]?',  # Dollar amounts
        r'revenue[:\s]+\$?[\d,]+\.?\d*[BMK]?',
        r'profit[:\s]+\$?[\d,]+\.?\d*[BMK]?',
        r'valuation[:\s]+\$?[\d,]+\.?\d*[BMK]?'
    ]
    
    for pattern in financial_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        metrics['financial_data'].extend(matches)
    
    # Growth metrics
    growth_patterns = [
        r'\d+%\s*growth',
        r'grew\s+\d+%',
        r'increased\s+\d+%',
        r'\d+%\s*increase'
    ]
    
    for pattern in growth_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        metrics['growth_metrics'].extend(matches)
    
    # Employee count
    employee_patterns = [
        r'\d+[\s,]*employees',
        r'team\s+of\s+\d+',
        r'workforce\s+of\s+\d+',
        r'\d+[\s,]*people'
    ]
    
    for pattern in employee_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        metrics['employee_count'].extend(matches)
    
    # Founding information
    founding_patterns = [
        r'founded\s+in\s+\d{4}',
        r'established\s+\d{4}',
        r'started\s+in\s+\d{4}',
        r'since\s+\d{4}'
    ]
    
    for pattern in founding_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        metrics['founding_info'].extend(matches)
    
    return metrics

def create_progress_tracker():
    """Create a progress tracker for the research process"""
    
    progress_container = st.container()
    
    with progress_container:
        st.write("### Research Progress")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        steps = [
            "Initializing agents...",
            "Searching web for company information...",
            "Extracting data from company website...",
            "Analyzing market position...",
            "Compiling final report...",
            "Complete!"
        ]
        
        return progress_bar, status_text, steps

def update_progress(progress_bar, status_text, step: int, total_steps: int, message: str):
    """Update progress bar and status"""
    
    progress = step / total_steps
    progress_bar.progress(progress)
    status_text.text(f"Step {step}/{total_steps}: {message}")

def display_error_message(error: str, suggestions: List[str] = None):
    """Display formatted error message with suggestions"""
    
    st.error(f"❌ **Error**: {error}")
    
    if suggestions:
        st.info("💡 **Suggestions:**")
        for suggestion in suggestions:
            st.write(f"• {suggestion}")

def display_success_message(message: str):
    """Display formatted success message"""
    
    st.success(f"✅ {message}")

def load_example_companies() -> List[Dict[str, str]]:
    """Load example companies for testing"""
    
    return [
        {"name": "OpenAI", "description": "AI research company"},
        {"name": "Tesla", "description": "Electric vehicle manufacturer"},
        {"name": "Microsoft", "description": "Technology corporation"},
        {"name": "Google", "description": "Technology company"},
        {"name": "Amazon", "description": "E-commerce and cloud computing"},
        {"name": "Apple", "description": "Technology company"},
        {"name": "Netflix", "description": "Streaming service"},
        {"name": "Uber", "description": "Ride-sharing platform"}
    ]

def export_to_json(data: Any, filename: str) -> bytes:
    """Export data to JSON format"""
    
    json_data = json.dumps(data, indent=2, ensure_ascii=False)
    return json_data.encode('utf-8')

def export_to_csv(data: Dict[str, Any], filename: str) -> str:
    """Export data to CSV format"""
    
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Section', 'Content'])
    
    # Write data
    for key, value in data.items():
        writer.writerow([key, str(value)])
    
    return output.getvalue()

def get_system_info() -> Dict[str, Any]:
    """Get system information for debugging"""
    
    return {
        'timestamp': datetime.now().isoformat(),
        'environment_vars': {
            'SERPER_API_KEY': bool(os.getenv('SERPER_API_KEY')),
            'FIRECRAWL_API_KEY': bool(os.getenv('FIRECRAWL_API_KEY')),
            'JINA_API_KEY': bool(os.getenv('JINA_API_KEY')),
            'OPENAI_API_KEY': bool(os.getenv('OPENAI_API_KEY'))
        },
        'session_state_keys': list(st.session_state.keys()) if 'st' in globals() else []
    }

# Rate limiting helper
class RateLimiter:
    def __init__(self, max_requests: int = 10, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
    
    def can_make_request(self) -> bool:
        now = time.time()
        # Remove old requests
        self.requests = [req_time for req_time in self.requests if now - req_time < self.time_window]
        
        return len(self.requests) < self.max_requests
    
    def make_request(self):
        if self.can_make_request():
            self.requests.append(time.time())
            return True
        return False

# Initialize rate limiter
rate_limiter = RateLimiter(max_requests=20, time_window=60)