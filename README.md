# Torrent Management Suite

A comprehensive Python-based torrent management suite that includes web scraping, automated downloading, and rate limiting functionality for qBittorrent. The suite is designed to handle large-scale torrent downloads safely without overwhelming your system.

## ⚠️ Important: System Protection

The main scraper (`main.py`) can easily find thousands of torrents in a single search. Starting all these downloads simultaneously will:
- Overwhelm your system resources
- Potentially crash qBittorrent
- May crash your entire system
- Cause network instability

**Always run the rate limiter (`qbit-rate-limiter.py`) before starting mass downloads!**

## Components and Workflow

1. **Scraper** (`main.py`): Finds and collects torrent information
2. **Rate Limiter** (`qbit-rate-limiter.py`): Prevents system overload
3. **CSV Processor** (`download-from-csv.py`): Manages batch downloads

### Recommended Usage Pattern

1. Start the rate limiter first:
   ```bash
   python qbit-rate-limiter.py
   ```

2. Then run your searches:
   ```bash
   python main.py "search query" --output results.csv
   ```

3. Optionally process saved results later:
   ```bash
   python download-from-csv.py
   ```

## Features

- 🔍 Torrent site scraping with support for 1337x (extensible to other sites)
- 🛡️ System protection through intelligent rate limiting
- 📥 Automated torrent downloading with qBittorrent integration
- 🚦 Queue management and download prioritization
- 📊 CSV export of search results
- ⚡ Asynchronous and concurrent processing
- 🔄 Batch processing of magnet links

## Prerequisites

- Python 3.7+
- qBittorrent with Web UI enabled
- Required Python packages:
  ```
  requests
  beautifulsoup4
  qbittorrent-api
  aiofiles
  tqdm
  ```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/TheRodzz/1337x-scraper.git
   cd 1337x-scraper
   ```

2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure qBittorrent:
   - Enable Web UI (Tools -> Preferences -> Web UI)
   - Set up username and password
   - Note down the port number (default: 8080)

## Component Details

### 1. Rate Limiter (`qbit-rate-limiter.py`)

**Critical for system stability!** The rate limiter:
- Prevents system crashes from mass downloads
- Manages download queue intelligently
- Prioritizes downloads based on progress and age
- Maintains system responsiveness

Configuration (edit in script):
```bash
python qbit-rate-limiter.py
```
- `max_active_downloads`: Maximum concurrent active downloads (recommended: 10-15)
- `max_resumed_torrents`: Maximum number of resumed torrents (recommended: 20-30)
- `host`: qBittorrent Web UI host (default: localhost:8081)
- `username`: Web UI username
- `password`: Web UI password

### 2. Torrent Scraping (`main.py`)

Search and collect torrent information:
```bash
python main.py "search query" --max-pages 5 --max-links 10 --output results.csv
```

Optionally, you can start downloading torrents right away:
```bash
python main.py "search query" --max-pages 5 --max-links 10 --download
```

Options:
- `<search_query>`: The search term for finding torrents (required)
- `--max-pages`: Maximum number of pages to scrape (optional)
- `--max-links`: Maximum number of links to process per page (optional)
- `--download`: Enable automatic downloading of torrents (optional)
- `--output`: Specify the output CSV file name (default: results.csv)

### 3. CSV Processor (`download-from-csv.py`)

For batch processing saved magnet links:
```bash
python download-from-csv.py
```

Features:
- Processes CSV files containing magnet links
- Adds torrents to qBittorrent in controlled batches
- Works with rate limiter to prevent overload

## System Requirements

Due to the potential for handling large numbers of torrents, recommended minimum specifications:
- 8GB RAM
- Multicore CPU
- Stable internet connection
- Sufficient storage space for downloads

## Error Handling

The suite includes comprehensive error handling for:
- Network connectivity issues
- qBittorrent Web UI availability
- Invalid magnet links
- Rate limiting and queue management
- File I/O operations
- System resource monitoring

## Logging

All components include detailed logging with:
- Timestamp
- Operation status
- Error details
- Progress information
- Resource usage metrics

## Best Practices

1. **Always run the rate limiter first**
2. Start with small searches to test system behavior
3. Monitor system resources during operation
4. Adjust rate limiter settings based on your system capabilities
5. Use the CSV processor for large batches of downloads
6. Keep qBittorrent updated to latest version

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Safety and Legal Considerations

This tool is intended for legal torrent downloads only. Users are responsible for:
- Complying with local laws and regulations
- Respecting copyright and intellectual property rights
- Using appropriate security measures
- Following acceptable use policies

## License

[MIT License](LICENSE)

## Disclaimer

This software is provided for educational purposes only. Users are responsible for ensuring compliance with local laws and regulations regarding torrent downloads.