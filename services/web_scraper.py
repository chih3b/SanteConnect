#!/usr/bin/env python3
"""
Web Scraper Service for Medical Information
Fallback when drug not found in local DB or MCP sources
"""

import requests
from bs4 import BeautifulSoup
import re
from typing import Optional, Dict
import time

# User agent to avoid blocks
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

TIMEOUT = 15


def clean_text(text: str) -> str:
    """Clean extracted text"""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def scrape_drugs_com(drug_name: str) -> Optional[Dict]:
    """Scrape drug information from Drugs.com"""
    try:
        # Try direct URL first
        drug_slug = drug_name.lower().replace(' ', '-').replace('/', '-')
        drug_url = f"https://www.drugs.com/{drug_slug}.html"
        
        response = requests.get(drug_url, headers=HEADERS, timeout=TIMEOUT)
        
        # If not found, try search
        if response.status_code != 200:
            search_url = f"https://www.drugs.com/search.php?searchterm={drug_name.replace(' ', '+')}"
            response = requests.get(search_url, headers=HEADERS, timeout=TIMEOUT)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Find first result
            results = soup.select('a[href*="/"]')
            drug_link = None
            for link in results:
                href = link.get('href', '')
                if '/mtm/' in href or href.endswith('.html'):
                    if drug_name.lower().split()[0] in href.lower():
                        drug_link = href
                        break
            
            if not drug_link:
                return None
            
            if not drug_link.startswith('http'):
                drug_url = f"https://www.drugs.com{drug_link}"
            else:
                drug_url = drug_link
            
            time.sleep(0.5)
            response = requests.get(drug_url, headers=HEADERS, timeout=TIMEOUT)
            if response.status_code != 200:
                return None
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        result = {
            'source': 'Drugs.com',
            'url': drug_url,
            'drug_name': drug_name,
            'found': True
        }
        
        # Get title
        title = soup.select_one('h1')
        if title:
            result['brand_name'] = clean_text(title.text)
        
        # Get content from main article
        content_div = soup.select_one('.contentBox, .ddc-main-content, article')
        if content_div:
            # Get all paragraphs
            paragraphs = content_div.select('p')
            if paragraphs:
                # First paragraph is usually the description
                result['uses'] = clean_text(paragraphs[0].text)[:500]
        
        # Try to get specific sections
        for section in soup.select('h2, h3'):
            section_text = section.text.lower()
            next_elem = section.find_next(['p', 'ul'])
            if not next_elem:
                continue
            
            content = clean_text(next_elem.text)[:500]
            
            if 'warning' in section_text:
                result['warnings'] = content
            elif 'side effect' in section_text:
                result['side_effects'] = content
            elif 'dosage' in section_text or 'dose' in section_text:
                result['dosage'] = content
            elif 'use' in section_text and 'uses' not in result:
                result['uses'] = content
        
        # Get meta description as fallback
        if 'uses' not in result:
            meta = soup.select_one('meta[name="description"]')
            if meta:
                result['uses'] = clean_text(meta.get('content', ''))[:500]
        
        return result if result.get('uses') or result.get('brand_name') else None
        
    except Exception as e:
        print(f"⚠️ Drugs.com error: {e}")
        return None


def scrape_medlineplus(drug_name: str) -> Optional[Dict]:
    """Scrape drug information from MedlinePlus (NIH)"""
    try:
        # Search URL
        search_url = f"https://medlineplus.gov/druginformation.html"
        
        # Try direct drug info URL
        drug_slug = drug_name.lower().replace(' ', '')
        drug_url = f"https://medlineplus.gov/druginfo/meds/a{drug_slug}.html"
        
        response = requests.get(drug_url, headers=HEADERS, timeout=TIMEOUT)
        
        if response.status_code != 200:
            # Try search
            search_url = f"https://vsearch.nlm.nih.gov/vivisimo/cgi-bin/query-meta?v%3Aproject=medlineplus&v%3Asources=medlineplus-bundle&query={drug_name.replace(' ', '+')}"
            return None  # MedlinePlus search is complex, skip for now
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        result = {
            'source': 'MedlinePlus (NIH)',
            'url': drug_url,
            'drug_name': drug_name,
            'found': True
        }
        
        # Get title
        title = soup.select_one('h1')
        if title:
            result['brand_name'] = clean_text(title.text)
        
        # Get sections
        for section in soup.select('.section'):
            header = section.select_one('h2')
            if not header:
                continue
            
            header_text = header.text.lower()
            body = section.select_one('.section-body')
            if not body:
                continue
            
            content = clean_text(body.text)[:500]
            
            if 'why' in header_text:
                result['uses'] = content
            elif 'side effect' in header_text:
                result['side_effects'] = content
            elif 'precaution' in header_text or 'warning' in header_text:
                result['warnings'] = content
            elif 'should' in header_text and 'take' in header_text:
                result['dosage'] = content
        
        return result if result.get('uses') else None
        
    except Exception as e:
        print(f"⚠️ MedlinePlus error: {e}")
        return None


def scrape_wikipedia(drug_name: str) -> Optional[Dict]:
    """Scrape drug information from Wikipedia"""
    try:
        # Wikipedia API for search
        search_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{drug_name.replace(' ', '_')}"
        
        response = requests.get(search_url, headers=HEADERS, timeout=TIMEOUT)
        if response.status_code != 200:
            return None
        
        data = response.json()
        
        if data.get('type') == 'disambiguation':
            return None
        
        result = {
            'source': 'Wikipedia',
            'url': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
            'drug_name': drug_name,
            'found': True,
            'brand_name': data.get('title', drug_name),
            'uses': data.get('extract', '')[:500]
        }
        
        return result if result.get('uses') else None
        
    except Exception as e:
        print(f"⚠️ Wikipedia error: {e}")
        return None


def scrape_rxlist(drug_name: str) -> Optional[Dict]:
    """Scrape drug information from RxList"""
    try:
        drug_slug = drug_name.lower().replace(' ', '-')
        drug_url = f"https://www.rxlist.com/{drug_slug}/drug.htm"
        
        response = requests.get(drug_url, headers=HEADERS, timeout=TIMEOUT)
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        result = {
            'source': 'RxList',
            'url': drug_url,
            'drug_name': drug_name,
            'found': True
        }
        
        title = soup.select_one('h1')
        if title:
            result['brand_name'] = clean_text(title.text)
        
        # Get first paragraph
        content = soup.select_one('.monograph-content p, article p')
        if content:
            result['uses'] = clean_text(content.text)[:500]
        
        return result if result.get('uses') else None
        
    except Exception as e:
        print(f"⚠️ RxList error: {e}")
        return None


def search_web_for_drug(drug_name: str) -> Dict:
    """
    Search multiple medical websites for drug information.
    
    Args:
        drug_name: Name of the medication to search
    
    Returns:
        Dictionary with drug information from web sources
    """
    print(f"🌐 Searching web for: {drug_name}")
    
    results = {
        'drug_name': drug_name,
        'found': False,
        'sources_checked': [],
        'data': []
    }
    
    # Try each source - Wikipedia first (most reliable API)
    scrapers = [
        ('Wikipedia', scrape_wikipedia),
        ('Drugs.com', scrape_drugs_com),
        ('RxList', scrape_rxlist),
        ('MedlinePlus', scrape_medlineplus),
    ]
    
    for source_name, scraper_func in scrapers:
        results['sources_checked'].append(source_name)
        try:
            data = scraper_func(drug_name)
            if data and data.get('found'):
                results['found'] = True
                results['data'].append(data)
                print(f"  ✅ Found on {source_name}")
                # Stop after finding 2 good sources
                if len(results['data']) >= 2:
                    break
        except Exception as e:
            print(f"  ❌ {source_name} error: {e}")
        
        time.sleep(0.3)
    
    # Combine data into summary
    if results['found'] and results['data']:
        primary = results['data'][0]
        results['summary'] = {
            'brand_name': primary.get('brand_name', drug_name),
            'uses': primary.get('uses', 'Information not available'),
            'side_effects': primary.get('side_effects', 'See source for details'),
            'warnings': primary.get('warnings', 'Consult healthcare provider'),
            'dosage': primary.get('dosage', 'Follow prescription'),
            'source_urls': [d.get('url') for d in results['data'] if d.get('url')]
        }
    
    return results


if __name__ == "__main__":
    result = search_web_for_drug("ibuprofen")
    print("\n=== RESULT ===")
    print(f"Found: {result['found']}")
    if result.get('summary'):
        print(f"Uses: {result['summary'].get('uses', 'N/A')[:200]}...")
