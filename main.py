import requests
from bs4 import BeautifulSoup
import concurrent.futures
from functools import partial
import logging
import argparse
import csv
from tqdm import tqdm
import time
import random
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from abc import ABC, abstractmethod
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure retries for requests
session = requests.Session()
retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))

class TorrentSite(ABC):
    def __init__(self, base_url, headers):
        self.base_url = base_url
        self.headers = headers

    @abstractmethod
    def get_search_url(self, query, page):
        pass

    @abstractmethod
    def extract_links(self, soup):
        pass

    @abstractmethod
    def extract_torrent_info(self, soup):
        pass

    def get_total_pages(self, soup):
        return 1  # Default implementation, override if needed

class Site1337x(TorrentSite):
    def __init__(self):
        super().__init__(
            'https://1337x.to',
            {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
        )

    def get_search_url(self, query, page):
        return f'{self.base_url}/search/{query}/{page}/'

    def extract_links(self, soup):
        return [f"{self.base_url}{a['href']}" for td in soup.find_all('td', class_='coll-1 name') for a in td.find_all('a')[1:2]]

    def extract_torrent_info(self, soup):
        info = {}
        info['title'] = soup.find('h1', class_='torrent-title').text.strip() if soup.find('h1', class_='torrent-title') else 'N/A'
        info['size'] = soup.find('span', class_='torrent-size').text.strip() if soup.find('span', class_='torrent-size') else 'N/A'
        info['seeders'] = soup.find('span', class_='seeds').text.strip() if soup.find('span', class_='seeds') else 'N/A'
        info['leechers'] = soup.find('span', class_='leeches').text.strip() if soup.find('span', class_='leeches') else 'N/A'
        magnet_link_element = soup.find('a', {'id': 'openPopup'})
        info['magnet_link'] = magnet_link_element['href'] if magnet_link_element else 'N/A'
        return info

    def get_total_pages(self, soup):
        pagination = soup.find('div', class_='pagination')
        if pagination:
            last_page_link = pagination.find('li', class_='last').a['href']
            return int(last_page_link.split('/')[-2])
        return 1

class ThePirateBay(TorrentSite):
    def __init__(self):
        super().__init__(
            'https://thepiratebay.org',
            {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
        )

    def get_search_url(self, query, page):
        return f'{self.base_url}/search/{query}/{page}/99/0'

    def extract_links(self, soup):
        return [a['href'] for a in soup.select('a.detLink')]

    def extract_torrent_info(self, soup):
        info = {}
        info['title'] = soup.select_one('div#title').text.strip() if soup.select_one('div#title') else 'N/A'
        info['size'] = soup.select_one('dt:contains("Size:") + dd').text.strip() if soup.select_one('dt:contains("Size:") + dd') else 'N/A'
        info['seeders'] = soup.select_one('dt:contains("Seeders:") + dd').text.strip() if soup.select_one('dt:contains("Seeders:") + dd') else 'N/A'
        info['leechers'] = soup.select_one('dt:contains("Leechers:") + dd').text.strip() if soup.select_one('dt:contains("Leechers:") + dd') else 'N/A'
        magnet_link_element = soup.select_one('a[href^="magnet:"]')
        info['magnet_link'] = magnet_link_element['href'] if magnet_link_element else 'N/A'
        return info

def download_magnet_link(magnet_link):
    try:
        command = ['qbittorrent', '--skip-dialog=true', magnet_link]
        subprocess.run(command, check=True)
        logger.info(f"Started download for: {magnet_link}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error downloading {magnet_link}: {e}")

def process_page(site, query, page, max_links=None, min_seeders=0, max_size=None, download=False):
    url = site.get_search_url(query, page)
    r = session.get(url, headers=site.headers)
    soup = BeautifulSoup(r.content, 'html.parser')
    links = site.extract_links(soup)
    if max_links:
        links = links[:max_links]
    results = []
    for link in links:
        time.sleep(random.uniform(1, 3))  # Random delay to avoid rate limiting
        r = session.get(link, headers=site.headers)
        soup = BeautifulSoup(r.content, 'html.parser')
        info = site.extract_torrent_info(soup)
        if int(info['seeders']) >= min_seeders and (not max_size or parse_size(info['size']) <= max_size):
            results.append(info)
            logger.info(f'Added torrent: {info["title"]}')
            if download:
                download_magnet_link(info["magnet_link"])
    return results


def parse_size(size_str):
    size, unit = size_str.split()
    size = float(size)
    if unit.lower() == 'gb':
        return size * 1024
    elif unit.lower() == 'mb':
        return size
    elif unit.lower() == 'kb':
        return size / 1024
    else:
        return 0

def scrape_torrent_links(site, query='', max_pages=None, max_links_per_page=None, min_seeders=0, max_size=None, download=False):
    if not query:
        return []

    r = session.get(site.get_search_url(query, 1), headers=site.headers)
    soup = BeautifulSoup(r.content, 'html.parser')
    total_pages = min(site.get_total_pages(soup), max_pages or float('inf'))

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_page = {
            executor.submit(
                partial(process_page, site, query, page, max_links_per_page, min_seeders, max_size, download)
            ): page for page in range(1, total_pages + 1)
        }
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
    parser = argparse.ArgumentParser(description="Multi-Site Torrent Scraper")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--site", choices=["1337x", "piratebay"], default="1337x", help="Torrent site to scrape")
    parser.add_argument("--max-pages", type=int, default=None, help="Maximum number of pages to scrape")
    parser.add_argument("--max-links", type=int, default=None, help="Maximum number of links per page")
    parser.add_argument("--min-seeders", type=int, default=0, help="Minimum number of seeders")
    parser.add_argument("--max-size", type=float, default=None, help="Maximum size in MB")
    parser.add_argument("--download", action="store_true", help="Download torrents automatically")
    parser.add_argument("--output", default="results.csv", help="Output CSV file name")
    args = parser.parse_args()

    site = Site1337x() if args.site == "1337x" else ThePirateBay()
    results = scrape_torrent_links(site, query=args.query, max_pages=args.max_pages, max_links_per_page=args.max_links,
                                   min_seeders=args.min_seeders, max_size=args.max_size)
    save_to_csv(results, args.output)