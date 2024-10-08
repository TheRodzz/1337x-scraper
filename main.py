import requests
from bs4 import BeautifulSoup
import subprocess
import concurrent.futures
from functools import partial

# Base URL and headers
BASE_URL = 'https://www.1337x.to'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
}

def download_magnet_link(magnet_link):
    try:
        command = ['qbittorrent', '--skip-dialog=true', magnet_link]
        subprocess.run(command, check=True)
        print(f"Started download for: {magnet_link}")
    except subprocess.CalledProcessError as e:
        print(f"Error downloading {magnet_link}: {e}")

def extract_magnet_link(torrent_page_url):
    r = requests.get(torrent_page_url, headers=HEADERS)
    soup = BeautifulSoup(r.content, 'html.parser')
    magnet_link_element = soup.find('a', {'id': 'openPopup'})
    return magnet_link_element['href'] if magnet_link_element else None

def get_links_from_page(query, page_num):
    url = f'{BASE_URL}/search/{query}/{page_num}/'
    r = requests.get(url, headers=HEADERS)
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
    magnet_links = []
    for link in links:
        magnet_link = extract_magnet_link(link)
        if magnet_link:
            magnet_links.append(magnet_link)
            print(f'Added link: {magnet_link}')
            download_magnet_link(magnet_link)
        else:
            print(f"No magnet link found for {link}")
    return magnet_links

def scrape_torrent_links(query='', max_pages=None, max_links_per_page=None):
    if not query:
        return []
    
    r = requests.get(f'{BASE_URL}/search/{query}/1/', headers=HEADERS)
    soup = BeautifulSoup(r.content, 'html.parser')
    total_pages = min(get_total_pages(soup), max_pages or float('inf'))
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_page = {executor.submit(partial(process_page, query, page, max_links_per_page)): page for page in range(1, total_pages + 1)}
        magnet_links = []
        for future in concurrent.futures.as_completed(future_to_page):
            page = future_to_page[future]
            try:
                magnet_links.extend(future.result())
                print(f"Completed processing page {page}")
            except Exception as exc:
                print(f'Page {page} generated an exception: {exc}')
    
    print(f"Extracted {len(magnet_links)} magnet links.")
    return magnet_links

if __name__ == "__main__":
    q = input('Enter search query: ')
    max_pages = int(input('Enter maximum number of pages to scrape (or 0 for all): ') or 0)
    max_links = int(input('Enter maximum number of links per page (or 0 for all): ') or 0)
    magnet_links = scrape_torrent_links(query=q, max_pages=max_pages or None, max_links_per_page=max_links or None)