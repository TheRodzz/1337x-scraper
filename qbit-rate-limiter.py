#!/usr/bin/env python3
import qbittorrentapi
import time
import logging
import sys
import requests
from typing import List, Dict
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QBitTorrentManager:
    def __init__(
        self,
        host: str = 'localhost:8081',
        username: str = 'admin',
        password: str = 'adminadmin',
        max_active_downloads: int = 10,
        max_resumed_torrents: int = 20,
        max_retries: int = 3,
        retry_delay: int = 5
    ):
        """Initialize QBitTorrent manager with connection and limit settings."""
        self.host = host
        self.username = username
        self.password = password
        self.max_active_downloads = max_active_downloads
        self.max_resumed_torrents = max_resumed_torrents
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.qbt_client = None

        # Initial connection
        self.connect_to_client()

    def verify_web_ui_access(self) -> bool:
        """Verify if qBittorrent Web UI is accessible with credentials."""
        try:
            # Format the login URL
            base_url = f"http://{self.host}"
            login_url = f"{base_url}/api/v2/auth/login"

            # Prepare login data
            login_data = {
                'username': self.username,
                'password': self.password
            }

            # Try to login
            session = requests.Session()
            response = session.post(login_url, data=login_data, timeout=5)

            if response.text == "Ok.":
                logger.info("Successfully verified Web UI access")
                return True
            else:
                logger.error(f"Failed to login to Web UI: {response.text}")
                return False

        except requests.exceptions.ConnectionError:
            logger.error(f"Could not connect to {self.host}")
            return False
        except requests.exceptions.Timeout:
            logger.error("Connection timed out")
            return False
        except Exception as e:
            logger.error(f"Error verifying Web UI access: {str(e)}")
            return False

    def connect_to_client(self) -> None:
        """Establish connection to qBittorrent client with retry mechanism."""
        if not self.verify_web_ui_access():
            logger.error(f"qBittorrent Web UI is not accessible at {self.host}")
            logger.error("Please ensure:")
            logger.error("1. qBittorrent is running")
            logger.error("2. Web UI is enabled (Tools -> Preferences -> Web UI)")
            logger.error(f"3. Web UI is accessible at http://{self.host}")
            logger.error("4. Username and password are correct")
            sys.exit(1)

        retries = 0
        while retries < self.max_retries:
            try:
                self.qbt_client = qbittorrentapi.Client(
                    host=f"http://{self.host}",  # Added http:// prefix
                    username=self.username,
                    password=self.password,
                    VERIFY_WEBUI_CERTIFICATE=False,
                    REQUESTS_ARGS={'timeout': 5}
                )
                self.qbt_client.auth_log_in()
                logger.info("Successfully connected to qBittorrent")
                break
            except Exception as e:
                retries += 1
                logger.error(f"Connection attempt {retries} failed: {str(e)}")
                if retries < self.max_retries:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    logger.error("Failed to connect after maximum retries")
                    raise

    def check_connection(self) -> bool:
        """Check if connection is still valid and reconnect if necessary."""
        try:
            self.qbt_client.app_version()
            return True
        except:
            logger.warning("Connection lost, attempting to reconnect...")
            try:
                self.connect_to_client()
                return True
            except:
                return False

    def get_torrent_states(self) -> Dict[str, List]:
        """Get current states of all torrents."""
        if not self.check_connection():
            return {'active_downloads': [], 'resumed_torrents': [], 'paused_torrents': []}

        try:
            torrents = self.qbt_client.torrents_info()
            active_downloads = []
            resumed_torrents = []
            paused_torrents = []
            for torrent in torrents:
                torrent_info = {
                    'hash': torrent.hash,
                    'added_on': torrent.added_on,
                    'progress': torrent.progress,
                    'size': torrent.size
                }
                
                if torrent.state in ['downloading', 'stalledDL']:
                    active_downloads.append(torrent_info)
                if torrent.state not in ['pausedDL', 'stalledUP']:
                    resumed_torrents.append(torrent_info)
                else:
                    paused_torrents.append(torrent_info)
            return {
                'active_downloads': active_downloads,
                'resumed_torrents': resumed_torrents,
                'paused_torrents': paused_torrents
            }
        except Exception as e:
            logger.error(f"Error getting torrent states: {str(e)}")
            return {'active_downloads': [], 'resumed_torrents': [], 'paused_torrents': []}

    def sort_torrents(self, torrents: List[Dict]) -> List[Dict]:
        """Sort torrents by priority (least complete first, then oldest)."""
        return sorted(torrents, key=lambda x: (x['progress'], x['added_on']))

    def manage_torrents(self):
        """Manage torrents according to configured limits."""
        try:
            states = self.get_torrent_states()
            active_downloads = states['active_downloads']
            resumed_torrents = states['resumed_torrents']
            paused_torrents = states['paused_torrents']

            # Handle exceeding limits - pause newest torrents first
            if len(active_downloads) > self.max_active_downloads:
                torrents_to_pause = sorted(
                    active_downloads[self.max_active_downloads:],
                    key=lambda x: (-x['progress'], -x['added_on'])
                )
                self.qbt_client.torrents_pause(
                    torrent_hashes=[t['hash'] for t in torrents_to_pause]
                )
                logger.info(f"Paused {len(torrents_to_pause)} torrents to maintain active download limit")

            if len(resumed_torrents) > self.max_resumed_torrents:
                torrents_to_pause = sorted(
                    resumed_torrents[self.max_resumed_torrents:],
                    key=lambda x: (-x['progress'], -x['added_on'])
                )
                self.qbt_client.torrents_pause(
                    torrent_hashes=[t['hash'] for t in torrents_to_pause]
                )
                logger.info(f"Paused {len(torrents_to_pause)} torrents to maintain resumed torrent limit")

            # Handle under limits - resume oldest, least complete torrents first
            space_for_active = self.max_active_downloads - len(active_downloads)
            space_for_resumed = self.max_resumed_torrents - len(resumed_torrents)

            if space_for_resumed > 0 and paused_torrents:
                sorted_paused = self.sort_torrents(paused_torrents)
                torrents_to_resume = sorted_paused[:space_for_resumed]
                self.qbt_client.torrents_resume(
                    torrent_hashes=[t['hash'] for t in torrents_to_resume]
                )
                logger.info(f"Resumed {len(torrents_to_resume)} torrents to utilize available slots")

            logger.info(
                f"Status: Active downloads: {len(active_downloads)}/{self.max_active_downloads}, "
                f"Resumed torrents: {len(resumed_torrents)}/{self.max_resumed_torrents}, "
                f"Paused torrents: {len(paused_torrents)}"
            )

        except Exception as e:
            logger.error(f"Error managing torrents: {str(e)}")

def main():
    """Main function to run the torrent manager."""
    # Create manager instance with your actual qBittorrent Web UI settings
    manager = QBitTorrentManager(
        host='localhost:8081',       # Change this to match your setup
        username='admin',            # Change this to match your setup
        password='adminadmin',       # Change this to match your setup
        max_active_downloads=20,
        max_resumed_torrents=40,
        max_retries=3,
        retry_delay=5
    )

    # Run continuous monitoring loop
    try:
        while True:
            manager.manage_torrents()
            time.sleep(10)  # Check every 30 seconds
    except KeyboardInterrupt:
        logger.info("Stopping torrent manager...")

if __name__ == "__main__":
    main()
