import requests
from bs4 import BeautifulSoup
import subprocess
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

# Base URL and headers
BASE_URL = 'https://www.1337x.to'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure retries for requests
session = requests.Session()
retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))

def download_magnet_link(magnet_link):
    try:
        command = ['qbittorrent', '--skip-dialog=true', magnet_link]
        subprocess.run(command, check=True)
        logger.info(f"Started download for: {magnet_link}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error downloading {magnet_link}: {e}")

def extract_torrent_info(soup, magnet_link):
    info = {}
    info['title'] = soup.find('h1', class_='torrent-title').text.strip() if soup.find('h1', class_='torrent-title') else 'N/A'
    info['size'] = soup.find('span', class_='torrent-size').text.strip() if soup.find('span', class_='torrent-size') else 'N/A'
    info['seeders'] = soup.find('span', class_='seeds').text.strip() if soup.find('span', class_='seeds') else 'N/A'
    info['leechers'] = soup.find('span', class_='leeches').text.strip() if soup.find('span', class_='leeches') else 'N/A'
    info['magnet_link'] = magnet_link
    return info

def extract_magnet_link(torrent_page_url):
    # time.sleep(random.uniform(1, 3))  # Random delay to avoid rate limiting
    r = session.get(torrent_page_url, headers=HEADERS)
    soup = BeautifulSoup(r.content, 'html.parser')
    magnet_link_element = soup.find('a', {'id': 'openPopup'})
    if magnet_link_element:
        magnet_link = magnet_link_element['href']
        info = extract_torrent_info(soup, magnet_link)
        return info
    return None

def get_links_from_page(query, page_num):
    url = f'{BASE_URL}/search/{query}/{page_num}/'
    r = session.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.content, 'html.parser')
    return [f"{BASE_URL}{a['href']}" for td in soup.find_all('td', class_='coll-1 name') for a in td.find_all('a')[1:2]]

def get_total_pages(soup):
    pagination = soup.find('div', class_='pagination')
    if pagination:
        last_page_link = pagination.find('li', class_='last').a['href']
        return int(last_page_link.split('/')[-2])
    return 1

def process_page(query, page, max_links=None):
    links = get_links_from_page(query, page)
    if max_links:
        links = links[:max_links]
    results = []
    for link in links:
        info = extract_magnet_link(link)
        if info:
            results.append(info)
            logger.info(f'Added link: {info["magnet_link"]}')
            if args.download:
                download_magnet_link(info["magnet_link"])
        else:
            logger.warning(f"No magnet link found for {link}")
    return results

def scrape_torrent_links(query='', max_pages=None, max_links_per_page=None):
    if not query:
        return []
    
    r = session.get(f'{BASE_URL}/search/{query}/1/', headers=HEADERS)
    soup = BeautifulSoup(r.content, 'html.parser')
    total_pages = min(get_total_pages(soup), max_pages or float('inf'))
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_page = {executor.submit(partial(process_page, query, page, max_links_per_page)): page for page in range(1, total_pages + 1)}
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

    results = scrape_torrent_links(query=args.query, max_pages=args.max_pages, max_links_per_page=args.max_links)
    save_to_csv(results, args.output)