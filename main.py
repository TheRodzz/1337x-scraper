from abc import ABC, abstractmethod  # To define abstract methods
import requests
from bs4 import BeautifulSoup
import subprocess
import concurrent.futures
from functools import partial
import logging
import argparse
import csv
from tqdm import tqdm
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Base Site class
class Site(ABC):  # Abstract Base Class (ABC)
    def __init__(self, base_url, headers):
        self.base_url = base_url
        self.headers = headers
        self.session = requests.Session()
        retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
    
    def get(self, url):
        try:
            response = self.session.get(url, headers=self.headers)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    @abstractmethod
    def extract_magnet_link(self, torrent_page_url):
        raise NotImplementedError("This method should be implemented by subclasses.")
    
    @abstractmethod
    def get_links_from_page(self, query, page_num):
        raise NotImplementedError("This method should be implemented by subclasses.")
    
    @abstractmethod
    def generate_search_url(self, query, page_num):
        """Generate the search URL for the specific site."""
        raise NotImplementedError("This method should be implemented by subclasses.")

# 1337x child class
class Torrent1337x(Site):
    def __init__(self):
        base_url = 'https://www.1337x.to'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }
        super().__init__(base_url, headers)

    def extract_torrent_info(self, soup, magnet_link):
        info = {}
        info['title'] = soup.find('h1', class_='torrent-title').text.strip() if soup.find('h1', class_='torrent-title') else 'N/A'
        info['size'] = soup.find('span', class_='torrent-size').text.strip() if soup.find('span', class_='torrent-size') else 'N/A'
        info['seeders'] = soup.find('span', class_='seeds').text.strip() if soup.find('span', class_='seeds') else 'N/A'
        info['leechers'] = soup.find('span', class_='leeches').text.strip() if soup.find('span', class_='leeches') else 'N/A'
        info['magnet_link'] = magnet_link
        return info

    def extract_magnet_link(self, torrent_page_url):
        soup = self.get(torrent_page_url)
        if not soup:
            return None

        magnet_link_element = soup.find('a', {'id': 'openPopup'})
        if magnet_link_element:
            magnet_link = magnet_link_element['href']
            return self.extract_torrent_info(soup, magnet_link)
        return None

    def get_links_from_page(self, query, page_num):
        url = self.generate_search_url(query, page_num)
        soup = self.get(url)
        if not soup:
            return []
        return [f"{self.base_url}{a['href']}" for td in soup.find_all('td', class_='coll-1 name') for a in td.find_all('a')[1:2]]

    def generate_search_url(self, query, page_num):
        """Generate search URL specific to 1337x"""
        return f'{self.base_url}/search/{query}/{page_num}/'

    def get_total_pages(self, soup):
        """Extract the total number of pages from the pagination."""
        if not soup:
            return 1
        pagination = soup.find('div', class_='pagination')
        if pagination:
            last_page_link = pagination.find('li', class_='last').a['href']
            return int(last_page_link.split('/')[-2])
        return 1
    #other sites can implement their own generate_search_url

def download_magnet_link(magnet_link):
    try:
        command = ['qbittorrent', '--skip-dialog=true', magnet_link]
        subprocess.run(command, check=True)
        logger.info(f"Started download for: {magnet_link}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error downloading {magnet_link}: {e}")

def process_page(site, query, page, max_links=None):
    links = site.get_links_from_page(query, page)
    if max_links:
        links = links[:max_links]
    results = []
    for link in links:
        info = site.extract_magnet_link(link)
        if info:
            results.append(info)
            logger.info(f'Added link: {info["magnet_link"]}')
            if args.download:
                download_magnet_link(info["magnet_link"])
        else:
            logger.warning(f"No magnet link found for {link}")
    return results

def scrape_torrent_links(site, query='', max_pages=None, max_links_per_page=None):
    if not query:
        return []
    
    r = site.get(site.generate_search_url(query, 1))
    total_pages = site.get_total_pages(r) if r else 1  # Make sure r is the soup object
    total_pages = min(total_pages, max_pages or float('inf'))
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_page = {executor.submit(partial(process_page, site, query, page, max_links_per_page)): page for page in range(1, total_pages + 1)}
        for future in tqdm(concurrent.futures.as_completed(future_to_page), total=len(future_to_page), desc="Processing pages"):
            page = future_to_page[future]
            try:
                results.extend(future.result())
                logger.info(f"Completed processing page {page}")
            except Exception as exc:
                logger.error(f'Page {page} generated an exception: {exc}')
    
    logger.info(f"Extracted {len(results)} torrent infos.")
    return results


def save_to_csv(results, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Title', 'Magnet Link', 'Size', 'Seeders', 'Leechers']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for info in results:
            writer.writerow({
                'Title': info['title'],
                'Magnet Link': info['magnet_link'],
                'Size': info['size'],
                'Seeders': info['seeders'],
                'Leechers': info['leechers']
            })
    logger.info(f"Results saved to {filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Torrent Scraper")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--max-pages", type=int, default=None, help="Maximum number of pages to scrape")
    parser.add_argument("--max-links", type=int, default=None, help="Maximum number of links per page")
    parser.add_argument("--download", action="store_true", help="Download torrents automatically")
    parser.add_argument("--output", default="results.csv", help="Output CSV file name")
    args = parser.parse_args()

    site = Torrent1337x()  # You can swap this with any other torrent site class you create
    results = scrape_torrent_links(site, query=args.query, max_pages=args.max_pages, max_links_per_page=args.max_links)
    save_to_csv(results, args.output)
    