# Enhanced Torrent Scraper

This Python script is an advanced torrent scraper that extracts information from the 1337x torrent site. It provides a flexible and efficient way to search for torrents, collect detailed information, and optionally download them.

## Features

- Search for torrents based on user-provided queries
- Concurrent scraping of multiple pages for improved performance
- Extraction of detailed torrent information (title, size, seeders, leechers, magnet link)
- Optional automatic downloading of torrents using qBittorrent
- CSV output for easy data analysis and processing
- Configurable maximum number of pages and links per page
- Progress bar to track scraping progress
- Robust error handling and logging
- Rate limiting to avoid overloading the target site

## Requirements

- Python 3.6+
- Required Python packages (listed in `requirements.txt`)
- qBittorrent (optional, for automatic downloading)

## Installation and Setup

You can set up this project using either standard Python virtual environments or Anaconda. Choose the method you prefer.

### Option 1: Standard Python Virtual Environment

1. Clone the repository:
   ```
   git clone https://github.com/TheRodzz/1337x-scraper.git
   cd 1337x-scraper
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS and Linux:
     ```
     source venv/bin/activate
     ```

4. Install the required packages:
   ```
   pip3 install -r requirements.txt
   ```

### Option 2: Anaconda Environment

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/torrent-scraper.git
   cd torrent-scraper
   ```

2. Create a new Anaconda environment:
   ```
   conda create --name torrent-scraper python=3.12
   ```

3. Activate the environment:
   ```
   conda activate torrent-scraper
   ```

4. Install the required packages:
   ```
   conda install --yes --file requirements.txt
   ```

### Optional: Install qBittorrent

If you plan to use the automatic download feature, install qBittorrent from the [official website](https://www.qbittorrent.org/download).

## Usage

Ensure your virtual environment is activated before running the script.

Run the script from the command line with the following syntax:

```
python torrent_scraper.py <search_query> [options]
```

### Command-line Arguments

- `<search_query>`: The search term for finding torrents (required)
- `--max-pages`: Maximum number of pages to scrape (optional)
- `--max-links`: Maximum number of links to process per page (optional)
- `--download`: Enable automatic downloading of torrents (optional)
- `--output`: Specify the output CSV file name (default: results.csv)

### Examples

1. Basic search:
   ```
   python3 torrent_scraper.py "ubuntu 20.04"
   ```

2. Limit the search to 3 pages with a maximum of 5 links per page:
   ```
   python3 torrent_scraper.py "python programming" --max-pages 3 --max-links 5
   ```

3. Search and automatically download torrents:
   ```
   python3 torrent_scraper.py "open source games" --download
   ```

4. Specify a custom output file:
   ```
   python3 torrent_scraper.py "data science books" --output data_science_torrents.csv
   ```

## Output

The script generates a CSV file (default: `results.csv`) with the following columns:

- Title
- Magnet Link
- Size
- Seeders
- Leechers

## Caution

- Be aware of the legal implications of downloading copyrighted material in your jurisdiction.
- Use this script responsibly and ethically.
- Respect the target website's terms of service and avoid overloading their servers.

## Disclaimer

This script is for educational purposes only. The authors are not responsible for any misuse or any consequences resulting from the use of this software.

## Contributing

Contributions, issues, and feature requests are welcome. Feel free to check [issues page](https://github.com/TheRodzz/1337x-scraper/issues) if you want to contribute.

## License

[MIT](https://choosealicense.com/licenses/mit/)