import logging
import requests
import tempfile
import os
import time
import zlib
import io
from typing import Optional, Dict, List, Union
from urllib.parse import urlparse, parse_qs
import hashlib
from pathlib import Path
from queue import PriorityQueue
from threading import Thread, Lock
from .config import DOWNLOAD_CONFIG, ERROR_MESSAGES

class RetryStrategy:
    def __init__(self, max_retries: int = 3, initial_delay: float = 1.0):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt using exponential backoff"""
        return min(300, self.initial_delay * (2 ** attempt))  # Max 5 minutes

class DownloadQueue:
    def __init__(self, max_concurrent: int = 3):
        self.queue = PriorityQueue()
        self.active = True
        self.max_concurrent = max_concurrent
        self.current_downloads = 0
        self.lock = Lock()
        self._start_worker_threads()
        
    def _start_worker_threads(self):
        """Start worker threads for download processing"""
        self.workers = [
            Thread(target=self._process_queue, daemon=True)
            for _ in range(self.max_concurrent)
        ]
        for worker in self.workers:
            worker.start()
            
    def add_download(self, url: str, priority: int = 1):
        """Add download to queue with priority (lower number = higher priority)"""
        self.queue.put((priority, url))
        
    def _process_queue(self):
        """Process downloads from the queue"""
        while self.active:
            try:
                priority, url = self.queue.get(timeout=1)
                with self.lock:
                    self.current_downloads += 1
                try:
                    downloader.download_audio(url)
                finally:
                    with self.lock:
                        self.current_downloads -= 1
                    self.queue.task_done()
            except:
                continue

    def stop(self):
        """Stop queue processing"""
        self.active = False
        for worker in self.workers:
            worker.join()

class CacheCompression:
    @staticmethod
    def compress_data(data: bytes) -> bytes:
        """Compress data using zlib"""
        return zlib.compress(data)
        
    @staticmethod
    def decompress_data(data: bytes) -> bytes:
        """Decompress data using zlib"""
        return zlib.decompress(data)

class AudioDownloader:
    def __init__(self):
        self.cache_dir = Path(DOWNLOAD_CONFIG['CACHE_DIR'])
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.retry_strategy = RetryStrategy(
            max_retries=DOWNLOAD_CONFIG['MAX_RETRIES']
        )
        self.download_queue = DownloadQueue()
        self.compression = CacheCompression()
        
    def download_audio(self, url: str, priority: int = 1) -> Optional[str]:
        """
        Download audio file from Google Drive URL with retry mechanism
        Returns: Path to downloaded file or None if failed
        """
        attempt = 0
        while attempt < self.retry_strategy.max_retries:
            try:
                return self._try_download(url)
            except requests.RequestException as e:
                attempt += 1
                if attempt >= self.retry_strategy.max_retries:
                    logging.error(f"Max retries reached for {url}: {e}")
                    return None
                    
                delay = self.retry_strategy.get_delay(attempt)
                logging.warning(f"Retry {attempt} for {url} after {delay}s")
                time.sleep(delay)
                
    def _try_download(self, url: str) -> Optional[str]:
        """Single download attempt with caching"""
        try:
            # Generate cache key from URL
            cache_key = hashlib.md5(url.encode()).hexdigest()
            cache_path = self.cache_dir / f"{cache_key}.mp3.gz"
            
            # Check cache first
            if cache_path.exists():
                logging.info(f"Using cached audio file: {cache_path}")
                return self._decompress_cached_file(cache_path)
            
            # Transform URL for direct download
            download_url = self._transform_drive_url(url)
            
            # Download with progress tracking
            response = self.session.get(
                download_url,
                stream=True,
                timeout=DOWNLOAD_CONFIG['TIMEOUT'],
                headers={'Accept-Encoding': 'gzip, deflate'}
            )
            response.raise_for_status()
            
            # Get total file size
            total_size = int(response.headers.get('content-length', 0))
            
            # Download and compress file in chunks
            compressed_data = io.BytesIO()
            if total_size > 0:
                downloaded = 0
                chunks = []
                for chunk in response.iter_content(chunk_size=DOWNLOAD_CONFIG['CHUNK_SIZE']):
                    if chunk:
                        chunks.append(chunk)
                        downloaded += len(chunk)
                        progress = (downloaded / total_size) * 100
                        logging.debug(f"Download progress: {progress:.1f}%")
                
                # Compress complete file
                full_data = b''.join(chunks)
                compressed_data.write(self.compression.compress_data(full_data))
            else:
                compressed_data.write(
                    self.compression.compress_data(response.content)
                )
            
            # Save compressed data to cache
            with open(cache_path, 'wb') as f:
                f.write(compressed_data.getvalue())
            
            return self._decompress_cached_file(cache_path)
            
        except Exception as e:
            logging.error(f"Error downloading file: {e}")
            return None

    def _decompress_cached_file(self, cache_path: Path) -> str:
        """Decompress cached file to temporary location"""
        try:
            temp_path = Path(tempfile.gettempdir()) / f"{cache_path.stem}.mp3"
            with open(cache_path, 'rb') as f:
                compressed_data = f.read()
            decompressed_data = self.compression.decompress_data(compressed_data)
            with open(temp_path, 'wb') as f:
                f.write(decompressed_data)
            return str(temp_path)
        except Exception as e:
            logging.error(f"Error decompressing cached file: {e}")
            return None

    def _transform_drive_url(self, url: str) -> str:
        """Transform Google Drive URL for direct download"""
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        
        # Remove view/open parameters
        query_params.pop('view', None)
        query_params.pop('open', None)
        
        # Add export parameter
        query_params['export'] = ['download']
        
        # Reconstruct URL
        new_query = '&'.join(f"{k}={v[0]}" for k, v in query_params.items())
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{new_query}"

    def queue_download(self, url: str, priority: int = 1):
        """Add download to queue"""
        self.download_queue.add_download(url, priority)

    def cleanup_cache(self, max_age_hours: int = 24):
        """Clean up old cached files"""
        try:
            current_time = time.time()
            for cache_file in self.cache_dir.glob("*.mp3.gz"):
                file_age = current_time - cache_file.stat().st_mtime
                if file_age > max_age_hours * 3600:
                    try:
                        cache_file.unlink()
                        logging.info(f"Removed old cache file: {cache_file}")
                    except Exception as e:
                        logging.error(f"Error removing cache file {cache_file}: {e}")
        except Exception as e:
            logging.error(f"Error cleaning cache: {e}")

    def __del__(self):
        """Cleanup on object destruction"""
        self.download_queue.stop()
        self.session.close()

# Singleton instance
downloader = AudioDownloader()

def download_google_drive_audio(url: str) -> Optional[str]:
    """Legacy wrapper function"""
    return downloader.download_audio(url)

def cleanup_old_files():
    """Clean up old temporary files"""
    downloader.cleanup_cache()

def queue_download(url: str, priority: int = 1):
    """Queue a download with priority"""
    downloader.queue_download(url, priority)