from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import requests
from bs4 import BeautifulSoup
import json

class WebsiteScraperInput(BaseModel):
    """Input schema for WebsiteScraper."""
    url: str = Field(..., description="The URL to scrape")

class WebsiteScraper(BaseTool):
    name: str = "Website Scraper"
    description: str = "Scrape content from a website URL"
    args_schema: Type[BaseModel] = WebsiteScraperInput

    def _run(self, url: str) -> str:
        """Scrape content from a website URL."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
                
            # Get text content
            text = soup.get_text()
            
            # Clean up the text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Limit the text length to avoid overwhelming the model
            if len(text) > 5000:
                text = text[:5000] + "..."
                
            return text
            
        except requests.exceptions.RequestException as e:
            return f"Error scraping website: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

class CompanyWebsiteFinderInput(BaseModel):
    """Input schema for CompanyWebsiteFinder."""
    company_name: str = Field(..., description="The name of the company to search for")

class CompanyWebsiteFinder(BaseTool):
    name: str = "Company Website Finder"
    description: str = "Find the official website of a company"
    args_schema: Type[BaseModel] = CompanyWebsiteFinderInput

    def _run(self, company_name: str) -> str:
        """Find the official website of a company using web search."""
        # This is a placeholder implementation
        # In a real scenario, you'd use a search API or web scraping
        search_query = f"{company_name} official website"
        
        # For demo purposes, return a formatted message
        return f"Searching for {company_name} official website. Please implement actual search logic here."

class DataExtractorInput(BaseModel):
    """Input schema for DataExtractor."""
    content: str = Field(..., description="The content to extract data from")
    data_type: str = Field(..., description="The type of data to extract (e.g., 'contact', 'products', 'about')")

class DataExtractor(BaseTool):
    name: str = "Data Extractor"
    description: str = "Extract specific types of data from content"
    args_schema: Type[BaseModel] = DataExtractorInput

    def _run(self, content: str, data_type: str) -> str:
        """Extract specific types of data from content."""
        content_lower = content.lower()
        
        if data_type.lower() == 'contact':
            # Look for contact information
            contact_keywords = ['contact', 'email', 'phone', 'address', 'support']
            extracted = []
            
            for keyword in contact_keywords:
                if keyword in content_lower:
                    # Find sentences containing the keyword
                    sentences = content.split('.')
                    for sentence in sentences:
                        if keyword in sentence.lower():
                            extracted.append(sentence.strip())
                            
            return '\n'.join(extracted[:5])  # Limit to 5 relevant sentences
            
        elif data_type.lower() == 'products':
            # Look for product information
            product_keywords = ['product', 'service', 'solution', 'offer']
            extracted = []
            
            for keyword in product_keywords:
                if keyword in content_lower:
                    sentences = content.split('.')
                    for sentence in sentences:
                        if keyword in sentence.lower():
                            extracted.append(sentence.strip())
                            
            return '\n'.join(extracted[:10])  # Limit to 10 relevant sentences
            
        elif data_type.lower() == 'about':
            # Look for about information
            about_keywords = ['about', 'company', 'mission', 'vision', 'founded', 'history']
            extracted = []
            
            for keyword in about_keywords:
                if keyword in content_lower:
                    sentences = content.split('.')
                    for sentence in sentences:
                        if keyword in sentence.lower():
                            extracted.append(sentence.strip())
                            
            return '\n'.join(extracted[:10])  # Limit to 10 relevant sentences
            
        else:
            return f"Data type '{data_type}' not supported. Supported types: contact, products, about"

# Create instances of the tools
scrape_website = WebsiteScraper()
find_company_website = CompanyWebsiteFinder()
extract_data = DataExtractor()