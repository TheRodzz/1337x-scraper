import csv
import asyncio
import logging
from asyncio import Queue
import aiofiles
from concurrent.futures import ThreadPoolExecutor
import subprocess
from typing import List, Dict
from dataclasses import dataclass
from datetime import datetime

# Set up logging with a simpler format that doesn't try to access 'extra'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

@dataclass
class TorrentInfo:
    category: str
    type: str
    language: str
    size: str
    uploaded_by: str
    downloads: int
    last_checked: str
    date_uploaded: str
    seeders: int
    leechers: int
    magnet_link: str

class MagnetProcessor:
    def __init__(self, batch_size: int = 5, max_concurrent: int = 3, min_seeders: int = 1):
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent
        self.min_seeders = min_seeders
        self.queue = Queue()
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent)
        self.processed_count = 0
        self.skipped_count = 0

    def _parse_csv_row(self, row: List[str]) -> TorrentInfo:
        """Parse a CSV row into a TorrentInfo object"""
        return TorrentInfo(
            category=row[0],
            type=row[1],
            language=row[2],
            size=row[3],
            uploaded_by=row[4],
            downloads=int(row[5]) if row[5].isdigit() else 0,
            last_checked=row[6],
            date_uploaded=row[7],
            seeders=int(row[8]) if row[8].isdigit() else 0,
            leechers=int(row[9]) if row[9].isdigit() else 0,
            magnet_link=row[10]
        )

    async def download_magnet_batch(self, torrents: List[TorrentInfo]):
        """Process a batch of magnet links concurrently"""
        try:
            commands = []
            for torrent in torrents:
                if torrent.seeders >= self.min_seeders:
                    cmd = [
                        'qbittorrent',
                        '--skip-dialog=true',
                        '--add-paused=true',
                        torrent.magnet_link
                    ]
                    commands.append((cmd, torrent))
                else:
                    self.skipped_count += 1
                    logger.info(
                        f"Skipping torrent: category={torrent.category}, "
                        f"size={torrent.size}, seeders={torrent.seeders}"
                    )

            # Execute commands concurrently using ThreadPoolExecutor
            tasks = []
            for cmd, torrent in commands:
                task = self.executor.submit(subprocess.run, cmd, check=True)
                tasks.append((task, torrent))

            # Wait for all tasks to complete
            for task, torrent in tasks:
                try:
                    task.result()
                    self.processed_count += 1
                    logger.info(
                        f"Successfully added torrent: category={torrent.category}, "
                        f"size={torrent.size}, seeders={torrent.seeders}"
                    )
                except subprocess.CalledProcessError as e:
                    logger.error(
                        f"Error adding torrent: category={torrent.category}, "
                        f"size={torrent.size}, error={str(e)}"
                    )

        except Exception as e:
            logger.error(f"Batch processing error: {e}")

    async def process_queue(self):
        """Process magnet links from the queue in batches"""
        while True:
            batch = []
            try:
                # Collect up to batch_size items from the queue
                for _ in range(self.batch_size):
                    try:
                        torrent = await asyncio.wait_for(self.queue.get(), timeout=0.5)
                        batch.append(torrent)
                    except asyncio.TimeoutError:
                        break

                if not batch:
                    break

                await self.download_magnet_batch(batch)

            except Exception as e:
                logger.error(f"Queue processing error: {e}")
            finally:
                # Mark tasks as done
                for _ in range(len(batch)):
                    self.queue.task_done()

    async def read_csv(self, csv_file: str):
        """Read magnet links from CSV file asynchronously"""
        try:
            async with aiofiles.open(csv_file, mode='r', encoding='utf-8') as file:
                content = await file.read()
                reader = csv.reader(content.splitlines())
                header = next(reader, None)  # Skip header

                if not header or len(header) != 11:
                    raise ValueError("Invalid CSV format")

                for row in reader:
                    if len(row) == 11:  # Ensure row has all required fields
                        try:
                            torrent_info = self._parse_csv_row(row)
                            await self.queue.put(torrent_info)
                        except ValueError as e:
                            logger.error(f"Error parsing row: {e}")
                    else:
                        logger.warning(f"Skipping invalid row: {row}")

        except FileNotFoundError:
            logger.error(f"File {csv_file} not found")
        except Exception as e:
            logger.error(f"Error reading CSV: {e}")

    async def process_file(self, csv_file: str):
        """Main processing function"""
        start_time = datetime.now()

        # Start CSV reading and queue processing concurrently
        await asyncio.gather(
            self.read_csv(csv_file),
            *(self.process_queue() for _ in range(self.max_concurrent))
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info(
            f"Processing completed - Processed: {self.processed_count}, "
            f"Skipped: {self.skipped_count}, Duration: {duration:.2f} seconds"
        )

def main():
    csv_file = 'results.csv'
    processor = MagnetProcessor(
        batch_size=15,
        max_concurrent=8,
        min_seeders=5  # Only process torrents with at least 5 seeders
    )

    # Run the async process
    try:
        asyncio.run(processor.process_file(csv_file))
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
    except Exception as e:
        logger.error(f"Process failed: {e}")
    finally:
        # Clean up
        processor.executor.shutdown()

if __name__ == "__main__":
    main()
