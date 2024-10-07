import requests
from bs4 import BeautifulSoup

# Base URL and headers
base_url = 'https://www.1337x.to'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
}

def extract_magnet_link(torrent_page_url):
    """ Extract the magnet link from a given torrent page """
    r = requests.get(torrent_page_url, headers=headers)
    soup = BeautifulSoup(r.content, 'html5lib')
    
    # Find the magnet link by searching for the <a> element with the given id and class
    magnet_link_element = soup.find('a', {'id': 'openPopup'})
    
    if magnet_link_element:
        return magnet_link_element['href']
    return None

def get_links_from_page(pageNum):
    """ Fetch the links from the search page """
    url = f'{base_url}/search/games/{pageNum}/'
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.content, 'html5lib')
    
    links = []
    for td in soup.find_all('td', class_='coll-1 name'):
        a_tag = td.find_all('a')[1]  # The second <a> contains the torrent link
        link = a_tag['href']
        full_link = f"{base_url}{link}"
        links.append(full_link)
    
    return links

def get_total_pages(soup):
    """ Extract total number of pages from pagination """
    pagination = soup.find('div', class_='pagination')
    if pagination:
        last_page_link = pagination.find('li', class_='last').a['href']
        total_pages = int(last_page_link.split('/')[-2])
        return total_pages
    return 1

def scrape_torrent_links(max_pages=None):
    """ Main function to scrape torrent links and magnet links """
    # Initial request to get total pages
    r = requests.get(f'{base_url}/search/games/1/', headers=headers)
    soup = BeautifulSoup(r.content, 'html5lib')
    total_pages = get_total_pages(soup)

    # If max_pages is provided and is less than total_pages, limit the number of pages
    if max_pages is not None and max_pages < total_pages:
        total_pages = max_pages

    # List to store all the magnet links
    magnet_links = []

    # Loop through each page, extract links, and then extract magnet links from those links
    for page in range(1, total_pages + 1):
        print(f"Extracting links from page {page} of {total_pages}...")
        links = get_links_from_page(page)
        
        for link in links:
            print(f"Processing {link}...")
            magnet_link = extract_magnet_link(link)
            
            if magnet_link:
                magnet_links.append(magnet_link)
            else:
                print(f"No magnet link found for {link}")

    # Now 'magnet_links' contains all the extracted magnet links.
    print(f"Extracted {len(magnet_links)} magnet links.")
    return magnet_links

# Example usage:
magnet_links = scrape_torrent_links(max_pages=2)  # Change or remove the argument to scrape all pages
print(magnet_links)  # You can print or process the list further as needed.
