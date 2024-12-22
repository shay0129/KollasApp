from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
import logging
import json
import os
import io
import time
from functools import lru_cache
from pathlib import Path
import hashlib
import shutil
from typing import Optional, Dict, List, Union, Any
from .config import GOOGLE_DRIVE_CONFIG, ERROR_MESSAGES

class FilePermissions:
    def __init__(self, service):
        self.service = service

    def share_file(self, file_id: str, email: str, role: str = 'reader') -> bool:
        """Share a file with specific permissions"""
        try:
            permission = {
                'type': 'user',
                'role': role,
                'emailAddress': email
            }
            self.service.permissions().create(
                fileId=file_id,
                body=permission,
                sendNotificationEmail=False
            ).execute()
            return True
        except Exception as e:
            logging.error(f"Error sharing file: {e}")
            return False

    def get_permissions(self, file_id: str) -> List[Dict]:
        """Get file permissions"""
        try:
            permissions = self.service.permissions().list(
                fileId=file_id
            ).execute()
            return permissions.get('permissions', [])
        except Exception as e:
            logging.error(f"Error getting permissions: {e}")
            return []

class FileVersioning:
    def __init__(self, service):
        self.service = service

    def get_versions(self, file_id: str) -> List[Dict]:
        """Get all versions of a file"""
        try:
            versions = self.service.revisions().list(fileId=file_id).execute()
            return versions.get('revisions', [])
        except Exception as e:
            logging.error(f"Error getting versions: {e}")
            return []

    def restore_version(self, file_id: str, revision_id: str) -> bool:
        """Restore a specific version of a file"""
        try:
            self.service.revisions().update(
                fileId=file_id,
                revisionId=revision_id
            ).execute()
            return True
        except Exception as e:
            logging.error(f"Error restoring version: {e}")
            return False

class GoogleDriveService:
    def __init__(self):
        self.service = None
        self.credentials = None
        self.cache_manager = CacheManager(GOOGLE_DRIVE_CONFIG['CACHE_DIR'])
        self.sync_manager = DriveSync(GOOGLE_DRIVE_CONFIG['SYNC_INTERVAL'])
        self.permissions = None
        self.versioning = None
        self.tags_manager = TagsManager()
        self._initialize_service()

    def _initialize_service(self):
        """Initialize Google Drive service with credentials"""
        try:
            self.credentials = self._load_credentials()
            if self.credentials:
                self.service = build('drive', 'v3', credentials=self.credentials)
                self.permissions = FilePermissions(self.service)
                self.versioning = FileVersioning(self.service)
                logging.info("Google Drive service initialized successfully")
        except Exception as e:
            logging.error(f"{ERROR_MESSAGES['SERVICE_INIT_FAILED']}: {e}")

    async def upload_file(
        self,
        file_path: str,
        parent_folder_id: str = None,
        file_metadata: Dict = None
    ) -> Optional[str]:
        """Upload a file to Google Drive"""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            metadata = {
                'name': os.path.basename(file_path),
                'parents': [parent_folder_id] if parent_folder_id else ['root']
            }
            
            if file_metadata:
                metadata.update(file_metadata)

            media = MediaFileUpload(
                file_path,
                resumable=True,
                chunksize=GOOGLE_DRIVE_CONFIG['UPLOAD_CHUNK_SIZE']
            )

            request = self.service.files().create(
                body=metadata,
                media_body=media,
                fields='id'
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    logging.debug(f"Upload progress: {int(status.progress() * 100)}%")

            file_id = response.get('id')
            
            # Add tags if provided
            if 'tags' in file_metadata:
                self.tags_manager.add_tags(file_id, file_metadata['tags'])

            return file_id

        except Exception as e:
            logging.error(f"Error uploading file: {e}")
            return None

    async def create_folder_hierarchy(self, structure: Dict, parent_id: str = 'root') -> Dict[str, str]:
        """Create a complete folder hierarchy and return mapping of names to IDs"""
        folder_mapping = {}
        
        try:
            for name, substructure in structure.items():
                folder_id = await self._create_or_get_folder(name, parent_id)
                folder_mapping[name] = folder_id
                
                if isinstance(substructure, dict):
                    subfolder_mapping = await self.create_folder_hierarchy(
                        substructure, folder_id
                    )
                    folder_mapping.update({
                        f"{name}/{subname}": subid 
                        for subname, subid in subfolder_mapping.items()
                    })
                    
            return folder_mapping
            
        except Exception as e:
            logging.error(f"Error creating folder hierarchy: {e}")
            return {}

    async def _create_or_get_folder(self, name: str, parent_id: str) -> str:
        """Create a folder if it doesn't exist, or get its ID if it does"""
        try:
            # Check if folder exists
            query = f"name = '{name}' and '{parent_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            results = self.service.files().list(q=query, fields='files(id)').execute()
            files = results.get('files', [])
            
            if files:
                return files[0]['id']
            
            # Create new folder
            folder_metadata = {
                'name': name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id]
            }
            
            folder = self.service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            
            return folder.get('id')
            
        except Exception as e:
            logging.error(f"Error creating/getting folder: {e}")
            raise

    # ... (rest of the existing methods)

class TagsManager:
    def __init__(self):
        self.tags_file = Path(GOOGLE_DRIVE_CONFIG['CACHE_DIR']) / 'file_tags.json'
        self.tags_cache = self._load_tags()

    def _load_tags(self) -> Dict:
        """Load tags from file"""
        if self.tags_file.exists():
            with open(self.tags_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_tags(self):
        """Save tags to file"""
        with open(self.tags_file, 'w') as f:
            json.dump(self.tags_cache, f)

    def add_tags(self, file_id: str, tags: List[str]):
        """Add tags to a file"""
        if file_id not in self.tags_cache:
            self.tags_cache[file_id] = []
        self.tags_cache[file_id].extend([t for t in tags if t not in self.tags_cache[file_id]])
        self._save_tags()

    def get_tags(self, file_id: str) -> List[str]:
        """Get tags for a file"""
        return self.tags_cache.get(file_id, [])

    def search_by_tags(self, tags: List[str]) -> List[str]:
        """Find files with specific tags"""
        return [
            file_id for file_id, file_tags in self.tags_cache.items()
            if all(tag in file_tags for tag in tags)
        ]

# Singleton instance
drive_service = GoogleDriveService()

# Legacy compatibility functions
def get_service():
    """Get the singleton service instance"""
    return drive_service.service

def get_sub_folders_and_files(service, folder_id):
    """Backward compatibility function"""
    return drive_service.get_folder_contents(folder_id)