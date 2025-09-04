# Path: scripts/web_scraper_maritime.py
# File: web_scraper_maritime.py
# Execute from: /Users/hugodiaz/Astoria/hf_spaces/astoria_open
# Purpose: Scrape maritime websites and save as vector-db ready documents

import os
import requests
import time
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathlib import Path
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MaritimeWebScraper:
    def __init__(self, output_dir="data/maritime_history"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.output_dir / "articles").mkdir(exist_ok=True)
        (self.output_dir / "periodicals").mkdir(exist_ok=True)
        (self.output_dir / "regulations").mkdir(exist_ok=True)
        (self.output_dir / "historical").mkdir(exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def scrape_article(self, url: str, category: str = "articles", delay: float = 1.0) -> bool:
        """
        Scrape a single article and save as text file
        """
        try:
            # Add delay to be respectful
            time.sleep(delay)
            
            logging.info(f"Scraping: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'advertisement']):
                element.decompose()
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else "Unknown Title"
            
            # Extract main content (try multiple selectors)
            content_selectors = [
                'article', 'main', '.content', '.post-content', 
                '.entry-content', '[role="main"]', '.article-body'
            ]
            
            content = None
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = content_elem.get_text(separator='\n\n').strip()
                    break
            
            # Fallback to body if no specific content found
            if not content:
                content = soup.get_text(separator='\n\n').strip()
            
            # Clean up content
            content = self.clean_text(content)
            
            if len(content) < 200:  # Skip very short content
                logging.warning(f"Content too short, skipping: {url}")
                return False
            
            # Generate filename
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            domain = urlparse(url).netloc.replace('www.', '')
            safe_title = "".join(c for c in title_text if c.isalnum() or c in (' ', '-', '_')).strip()[:50]
            filename = f"{safe_title}_{domain}_{url_hash}.txt"
            
            # Create full document with metadata
            document_content = self.format_document(title_text, url, content, category)
            
            # Save to file
            output_path = self.output_dir / category / filename
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(document_content)
            
            logging.info(f"Saved: {output_path}")
            return True
            
        except Exception as e:
            logging.error(f"Error scraping {url}: {e}")
            return False

    def clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if len(line) > 0 and not line.startswith(('Cookie', 'JavaScript', 'Advertisement')):
                cleaned_lines.append(line)
        
        # Remove excessive whitespace
        content = '\n'.join(cleaned_lines)
        while '\n\n\n' in content:
            content = content.replace('\n\n\n', '\n\n')
        
        return content.strip()

    def format_document(self, title: str, url: str, content: str, category: str) -> str:
        """Format document with metadata for better vector search"""
        timestamp = datetime.now().isoformat()
        
        return f"""# {title}

**Source:** {url}
**Category:** {category}
**Scraped:** {timestamp}
**Type:** Maritime Documentation

---

{content}

---
*End of Document*
"""

    def scrape_maritime_sites(self):
        """
        Scrape predefined maritime websites
        """
        
        # Maritime Authority Sites
        authority_sites = [
            ("https://www.imo.org/en/MediaCentre/PressBriefings/pages/default.aspx", "regulations"),
            ("https://www.marad.dot.gov/news/", "regulations"),
            ("https://www.uscg.mil/News/", "regulations"),
        ]
        
        # Maritime News & Periodicals
        news_sites = [
            ("https://www.maritime-executive.com/", "periodicals"),
            ("https://gcaptain.com/", "periodicals"),
            ("https://www.marinelink.com/news", "periodicals"),
            ("https://www.seatrade-maritime.com/news", "periodicals"),
        ]
        
        # Historical & Educational
        educational_sites = [
            ("https://www.history.navy.mil/", "historical"),
            ("https://www.smithsonianmag.com/tag/maritime-history/", "historical"),
        ]
        
        all_sites = authority_sites + news_sites + educational_sites
        
        logging.info(f"Starting to scrape {len(all_sites)} maritime sites...")
        
        for url, category in all_sites:
            try:
                # Get the main page
                response = self.session.get(url)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find article links
                article_links = []
                for link in soup.find_all('a', href=True):
                    href = urljoin(url, link['href'])
                    if self.is_article_link(href):
                        article_links.append(href)
                
                # Scrape first 5 articles from each site
                for article_url in article_links[:5]:
                    self.scrape_article(article_url, category)
                    
            except Exception as e:
                logging.error(f"Error processing site {url}: {e}")
                continue

    def is_article_link(self, url: str) -> bool:
        """Determine if a URL looks like an article"""
        url_lower = url.lower()
        
        # Skip non-article patterns
        skip_patterns = [
            '/tag/', '/category/', '/author/', '/page/', '.pdf', '.jpg', '.png',
            'javascript:', 'mailto:', '#', '/search', '/login', '/register'
        ]
        
        for pattern in skip_patterns:
            if pattern in url_lower:
                return False
        
        # Look for article patterns
        article_patterns = [
            '/news/', '/article/', '/story/', '/post/', '/blog/',
            '/press-release/', '/announcement/', '/update/'
        ]
        
        return any(pattern in url_lower for pattern in article_patterns)

    def scrape_custom_urls(self, urls_with_categories: list):
        """
        Scrape custom list of URLs
        Format: [(url, category), ...]
        """
        logging.info(f"Scraping {len(urls_with_categories)} custom URLs...")
        
        for url, category in urls_with_categories:
            self.scrape_article(url, category, delay=2.0)  # Longer delay for custom scraping

def main():
    """Main execution function"""
    scraper = MaritimeWebScraper()
    
    # Option 1: Scrape predefined maritime sites
    print("1. Scrape predefined maritime websites")
    print("2. Scrape custom URL list")
    
    choice = input("Choose option (1 or 2): ").strip()
    
    if choice == "1":
        scraper.scrape_maritime_sites()
    
    elif choice == "2":
        # Example custom URLs - replace with your targets
        custom_urls = [
            ("https://www.maritime-executive.com/article/new-shipping-regulations-2024", "regulations"),
            ("https://gcaptain.com/maritime-safety-guidelines", "regulations"),
            # Add your specific URLs here
        ]
        
        scraper.scrape_custom_urls(custom_urls)
    
    else:
        print("Invalid choice")
        return
    
    print(f"\n✅ Scraping complete! Check the {scraper.output_dir} directory.")
    print("Next step: Run the ingestion script to load into vector database.")

if __name__ == "__main__":
    main()

#end-of-script