import csv
import asyncio
import logging
from asyncio import Queue
import aiofiles
from concurrent.futures import ThreadPoolExecutor
import subprocess
from typing import List

# Set up logging with a more efficient format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class MagnetProcessor:
    def __init__(self, batch_size: int = 5, max_concurrent: int = 3):
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent
        self.queue = Queue()
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent)

    async def download_magnet_batch(self, magnet_links: List[str]):
        """Process a batch of magnet links concurrently"""
        try:
            commands = [
                ['qbittorrent', '--skip-dialog=true', '--add-paused=true', link]
                for link in magnet_links
            ]

            # Execute commands concurrently using ThreadPoolExecutor
            tasks = [
                self.executor.submit(subprocess.run, cmd, check=True)
                for cmd in commands
            ]

            # Wait for all tasks to complete
            for task in tasks:
                try:
                    task.result()
                except subprocess.CalledProcessError as e:
                    logger.error(f"Error in batch download: {e}")

            logger.info(f"Processed batch of {len(magnet_links)} links")

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
                        link = await asyncio.wait_for(self.queue.get(), timeout=0.5)
                        batch.append(link)
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
            async with aiofiles.open(csv_file, mode='r') as file:
                content = await file.read()
                reader = csv.reader(content.splitlines())
                next(reader, None)  # Skip header

                for row in reader:
                    if len(row) > 1:
                        await self.queue.put(row[1])

        except FileNotFoundError:
            logger.error(f"File {csv_file} not found")
        except Exception as e:
            logger.error(f"Error reading CSV: {e}")

    async def process_file(self, csv_file: str):
        """Main processing function"""
        # Start CSV reading and queue processing concurrently
        await asyncio.gather(
            self.read_csv(csv_file),
            *(self.process_queue() for _ in range(self.max_concurrent))
        )

def main():
    csv_file = 'flac.csv'
    processor = MagnetProcessor(batch_size=15, max_concurrent=8)

    # Run the async process
    asyncio.run(processor.process_file(csv_file))

    # Clean up
    processor.executor.shutdown()

if __name__ == "__main__":
    main()
