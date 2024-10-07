import requests
from bs4 import BeautifulSoup

query = 'games'
pageNum = 1
url = f'https://www.1337x.to/search/{query}/{pageNum}/'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
}

r = requests.get(url, headers=headers)
soup = BeautifulSoup(r.content, 'html5lib')

for td in soup.find_all('td', class_='coll-1 name'):
    # Find the second <a> tag (the one with the link to the torrent)
    a_tag = td.find_all('a')[1]
    link = a_tag['href']  # Extract the link
    full_link = f"https://www.1337x.to{link}"  # Complete the link with the base URL

    print(full_link)
