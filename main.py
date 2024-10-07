import requests
from bs4 import BeautifulSoup

# Base query
query = 'games'
base_url = 'https://www.1337x.to'

# Headers to simulate a real browser request
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
}

def get_links_from_page(pageNum):
    # Request the specific search page
    url = f'{base_url}/search/{query}/{pageNum}/'
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.content, 'html5lib')
    
    # Find all <td> elements with class "coll-1 name" and extract links
    links = []
    for td in soup.find_all('td', class_='coll-1 name'):
        a_tag = td.find_all('a')[1]  # The second <a> contains the torrent link
        link = a_tag['href']
        full_link = f"{base_url}{link}"  # Construct full URL
        links.append(full_link)
    
    return links

def get_total_pages(soup):
    # Locate the pagination div and find the last page number
    pagination = soup.find('div', class_='pagination')
    if pagination:
        last_page_link = pagination.find('li', class_='last').a['href']
        total_pages = int(last_page_link.split('/')[-2])  # Extract the page number from the URL
        return total_pages
    return 1  # If no pagination, there's only one page

# Get the first page to determine the total number of pages
r = requests.get(f'{base_url}/search/{query}/1/', headers=headers)
soup = BeautifulSoup(r.content, 'html5lib')
total_pages = get_total_pages(soup)

# Now loop through all pages to extract the links
all_links = []

for page in range(1, total_pages + 1):
    print(f"Extracting links from page {page} of {total_pages}...")
    links = get_links_from_page(page)
    all_links.extend(links)

# Now, 'all_links' contains all the links from all pages.
print(f"Extracted {len(all_links)} links.")
print(all_links)  
