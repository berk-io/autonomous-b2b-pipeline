"""
B2B Data Extraction and Lead Generation Module

This module handles the automated discovery and extraction of business contact 
information from target domains. It employs robust request handling, rate-limit 
compliance, and regex-based data parsing to ensure data integrity and reliability.
"""

import re
import time
import logging
from typing import Set, Optional
import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class DataExtractor:
    def __init__(self, timeout: int = 15) -> None:
        self.timeout = timeout
        # Critical state: Session management for persistent connections
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        })

    def _extract_emails_from_html(self, html_content: str) -> Set[str]:
        # Critical state: Regex pattern for data integrity
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        raw_emails = re.findall(email_pattern, html_content)
        
        valid_emails = set()
        for email in raw_emails:
            email_lower = email.lower()
            # Excluding common generic image/asset extensions that match regex
            if not any(email_lower.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.css', '.js']):
                valid_emails.add(email_lower)
                
        return valid_emails

    def process_target(self, target_url: str) -> Optional[Set[str]]:
        try:
            if not target_url.startswith('http'):
                target_url = f"https://{target_url}"

            logging.info("Initiating data extraction pipeline for %s", target_url)
            response = self.session.get(target_url, timeout=self.timeout)
            response.raise_for_status()

            emails = self._extract_emails_from_html(response.text)
            
            # If no emails found on main page, attempting to crawl contact pages
            if not emails:
                soup = BeautifulSoup(response.text, 'html.parser')
                contact_links = soup.find_all('a', href=re.compile(r'(contact|about|iletişim)', re.IGNORECASE))
                
                for link in contact_links:
                    href = link.get('href')
                    if href:
                        if not href.startswith('http'):
                            href = target_url.rstrip('/') + '/' + href.lstrip('/')
                            
                        logging.info("Exploring secondary endpoint: %s", href)
                        # Critical state: Request throttling to prevent blocks
                        time.sleep(2.5) 
                        
                        try:
                            contact_resp = self.session.get(href, timeout=self.timeout)
                            emails.update(self._extract_emails_from_html(contact_resp.text))
                        except requests.RequestException:
                            logging.warning("Failed to retrieve secondary endpoint: %s", href)
                            continue

            logging.info("Extraction complete for %s. Found %d valid endpoints.", target_url, len(emails))
            return emails if emails else None

        except requests.exceptions.Timeout:
            logging.error("Connection timeout while reaching target: %s", target_url)
            return None
        except requests.exceptions.RequestException as e:
            logging.error("Request handling failed for %s: %s", target_url, str(e))
            return None
        except Exception as e:
            logging.error("Unexpected pipeline error for %s: %s", target_url, str(e))
            return None