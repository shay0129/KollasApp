"""
KollasApp Services Module

This module handles external services and API interactions:
- Google Drive integration for audio files storage, retrieval and management
- Audio file downloading, caching and compression
- File permissions and versioning
- Background download queue management

Main Components:
---------------
1. Google Drive Service:
   - File and folder management
   - Permissions control
   - Version tracking
   - Tag management
   - Caching system

2. Audio Downloader:
   - Priority-based download queue
   - Automatic retries
   - Cache compression
   - Background downloads
   - Progress tracking

Configuration:
-------------
Service settings can be modified in config.py
"""

from .google_services import (
    GoogleDriveService,
    get_service,
    get_sub_folders_and_files,
    FilePermissions,
    FileVersioning,
    TagsManager
)

from .requests import (
    AudioDownloader,
    download_google_drive_audio,
    cleanup_old_files,
    queue_download,
    RetryStrategy,
    DownloadQueue,
    CacheCompression
)

__all__ = [
    # Google Drive related
    'GoogleDriveService',
    'get_service',
    'get_sub_folders_and_files',
    'FilePermissions',
    'FileVersioning',
    'TagsManager',
    
    # Download related
    'AudioDownloader',
    'download_google_drive_audio',
    'cleanup_old_files',
    'queue_download',
    'RetryStrategy',
    'DownloadQueue',
    'CacheCompression'
]

# Version information
__version__ = '1.0.0'
__author__ = 'Your Name'
__description__ = 'Services module for KollasApp - Preserving Cochin Jewish Heritage'