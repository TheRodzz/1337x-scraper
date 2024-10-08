import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QFileDialog, QProgressBar
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from main import Site1337x, ThePirateBay, scrape_torrent_links, save_to_csv

class ScraperWorker(QThread):
    update_progress = pyqtSignal(int)
    update_log = pyqtSignal(str)
    finished = pyqtSignal(list)

    def __init__(self, site, query, max_pages, max_links, min_seeders, max_size):
        super().__init__()
        self.site = site
        self.query = query
        self.max_pages = max_pages
        self.max_links = max_links
        self.min_seeders = min_seeders
        self.max_size = max_size

    def run(self):
        results = scrape_torrent_links(
            self.site,
            query=self.query,
            max_pages=self.max_pages,
            max_links_per_page=self.max_links,
            min_seeders=self.min_seeders,
            max_size=self.max_size,
            download=True,
        )
        self.finished.emit(results)

class TorrentScraperGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Torrent Scraper')
        self.setGeometry(100, 100, 600, 400)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Search query
        query_layout = QHBoxLayout()
        query_layout.addWidget(QLabel('Search Query:'))
        self.query_input = QLineEdit()
        query_layout.addWidget(self.query_input)
        layout.addLayout(query_layout)

        # Site selection
        site_layout = QHBoxLayout()
        site_layout.addWidget(QLabel('Torrent Site:'))
        self.site_combo = QComboBox()
        self.site_combo.addItems(['1337x', 'The Pirate Bay'])
        site_layout.addWidget(self.site_combo)
        layout.addLayout(site_layout)

        # Max pages
        max_pages_layout = QHBoxLayout()
        max_pages_layout.addWidget(QLabel('Max Pages:'))
        self.max_pages_spin = QSpinBox()
        self.max_pages_spin.setRange(1, 100)
        self.max_pages_spin.setValue(1)
        max_pages_layout.addWidget(self.max_pages_spin)
        layout.addLayout(max_pages_layout)

        # Max links per page
        max_links_layout = QHBoxLayout()
        max_links_layout.addWidget(QLabel('Max Links per Page:'))
        self.max_links_spin = QSpinBox()
        self.max_links_spin.setRange(1, 100)
        self.max_links_spin.setValue(20)
        max_links_layout.addWidget(self.max_links_spin)
        layout.addLayout(max_links_layout)

        # Min seeders
        min_seeders_layout = QHBoxLayout()
        min_seeders_layout.addWidget(QLabel('Min Seeders:'))
        self.min_seeders_spin = QSpinBox()
        self.min_seeders_spin.setRange(0, 10000)
        min_seeders_layout.addWidget(self.min_seeders_spin)
        layout.addLayout(min_seeders_layout)

        # Max size
        max_size_layout = QHBoxLayout()
        max_size_layout.addWidget(QLabel('Max Size (MB):'))
        self.max_size_spin = QDoubleSpinBox()
        self.max_size_spin.setRange(0, 100000)
        self.max_size_spin.setValue(0)
        max_size_layout.addWidget(self.max_size_spin)
        layout.addLayout(max_size_layout)

        # Start button
        self.start_button = QPushButton('Start Scraping')
        self.start_button.clicked.connect(self.start_scraping)
        layout.addWidget(self.start_button)

        # Progress bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # Log output
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        # Save button
        self.save_button = QPushButton('Save Results')
        self.save_button.clicked.connect(self.save_results)
        self.save_button.setEnabled(False)
        layout.addWidget(self.save_button)

        self.results = None

    def start_scraping(self):
        self.start_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.log_output.clear()
        self.progress_bar.setValue(0)

        site = Site1337x() if self.site_combo.currentText() == '1337x' else ThePirateBay()
        query = self.query_input.text()
        max_pages = self.max_pages_spin.value()
        max_links = self.max_links_spin.value()
        min_seeders = self.min_seeders_spin.value()
        max_size = self.max_size_spin.value() if self.max_size_spin.value() > 0 else None

        self.worker = ScraperWorker(site, query, max_pages, max_links, min_seeders, max_size)
        self.worker.update_progress.connect(self.update_progress)
        self.worker.update_log.connect(self.update_log)
        self.worker.finished.connect(self.scraping_finished)
        self.worker.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_log(self, message):
        self.log_output.append(message)

    def scraping_finished(self, results):
        self.results = results
        self.log_output.append(f"Scraping finished. Found {len(results)} results.")
        self.start_button.setEnabled(True)
        self.save_button.setEnabled(True)

    def save_results(self):
        if not self.results:
            return

        file_name, _ = QFileDialog.getSaveFileName(self, "Save CSV File", "", "CSV Files (*.csv)")
        if file_name:
            save_to_csv(self.results, file_name)
            self.log_output.append(f"Results saved to {file_name}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TorrentScraperGUI()
    ex.show()
    sys.exit(app.exec_())