from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtCore import Qt, QTimer, pyqtSignal

import logging
from typing import Optional, List, Dict
from services.google_services import drive_service
from .custom_widgets import BookPage, AudioPlayer, LyricsViewer
from managers.audio_processor import AudioProcessor

class DisplayManager(QObject):
    """Content display manager"""
    
    contentChanged = pyqtSignal(dict)  # Signal for content changes
    errorOccurred = pyqtSignal(str)    # Signal for errors
    
    def __init__(self):
        super().__init__()
        self.current_path = []
        self.current_view = "all"  # all, favorites, recent, etc.
        self.audio_processor = AudioProcessor()
        
    def display_folder_contents(self, folder_id: str) -> List[Dict]:
        """Display folder contents"""
        try:
            contents = drive_service.get_folder_contents(folder_id)
            self.contentChanged.emit({
                'type': 'folder_contents',
                'data': contents,
                'path': self.current_path
            })
            return contents
        except Exception as e:
            logging.error(f"Error displaying folder contents: {e}")
            self.errorOccurred.emit(f"Error loading folder: {str(e)}")
            return []
            
    def navigate_to_folder(self, folder_id: str):
        """Navigate to folder"""
        self.current_path.append(folder_id)
        self.display_folder_contents(folder_id)
        
    def navigate_back(self):
        """Navigate back"""
        if self.current_path:
            self.current_path.pop()
            folder_id = self.current_path[-1] if self.current_path else None
            self.display_folder_contents(folder_id)
            
    def display_favorites(self):
        """Display favorites"""
        try:
            favorites = drive_service.get_favorite_files()
            self.contentChanged.emit({
                'type': 'favorites',
                'data': favorites
            })
        except Exception as e:
            logging.error(f"Error displaying favorites: {e}")
            self.errorOccurred.emit("Error loading favorites")
            
    def display_recent(self):
        """Display recent items"""
        try:
            recent = drive_service.get_recent_files()
            self.contentChanged.emit({
                'type': 'recent',
                'data': recent
            })
        except Exception as e:
            logging.error(f"Error displaying recent items: {e}")
            self.errorOccurred.emit("Error loading recent items")
            
    def search_content(self, query: str):
        """Search content"""
        try:
            results = drive_service.search_files(query)
            self.contentChanged.emit({
                'type': 'search_results',
                'data': results,
                'query': query
            })
        except Exception as e:
            logging.error(f"Error searching content: {e}")
            self.errorOccurred.emit("Error during search")
            
    def filter_content(self, content_type: str = None):
        """Filter content by type"""
        try:
            if self.current_path:
                contents = self.display_folder_contents(self.current_path[-1])
                if content_type:
                    contents = [
                        item for item in contents 
                        if item.get('mimeType', '').startswith(content_type)
                    ]
                self.contentChanged.emit({
                    'type': 'filtered_content',
                    'data': contents,
                    'filter': content_type
                })
        except Exception as e:
            logging.error(f"Error filtering content: {e}")
            self.errorOccurred.emit("Error filtering content")

class ContentViewWidget(QWidget):
    """Widget for content display"""
    
    itemSelected = pyqtSignal(dict)  # Signal for item selection
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.display_manager = DisplayManager()
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout(self)
        
        # Toolbar
        self.toolbar = QToolBar()
        self.back_btn = QAction("Back", self)
        self.view_mode = QComboBox()
        self.view_mode.addItems(["All", "Favorites", "Recent"])
        
        self.toolbar.addAction(self.back_btn)
        self.toolbar.addWidget(self.view_mode)
        
        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.toolbar.addWidget(self.search_bar)
        
        layout.addWidget(self.toolbar)
        
        # Split view
        splitter = QSplitter(Qt.Horizontal)
        
        # Categories tree
        self.category_tree = QTreeWidget()
        self.category_tree.setHeaderLabel("Categories")
        splitter.addWidget(self.category_tree)
        
        # Content area
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        
        # Content list
        self.content_list = QListWidget()
        content_layout.addWidget(self.content_list)
        
        # Audio player
        self.audio_player = AudioPlayer()
        content_layout.addWidget(self.audio_player)
        
        # Lyrics viewer
        self.lyrics_viewer = LyricsViewer()
        content_layout.addWidget(self.lyrics_viewer)
        
        splitter.addWidget(content_area)
        layout.addWidget(splitter)
        
    def _connect_signals(self):
        """Connect signals"""
        # Navigation signals
        self.back_btn.triggered.connect(self.display_manager.navigate_back)
        self.view_mode.currentTextChanged.connect(self._handle_view_change)
        self.search_bar.textChanged.connect(self._handle_search)
        
        # Content signals
        self.category_tree.itemClicked.connect(self._handle_category_select)
        self.content_list.itemClicked.connect(self._handle_item_select)
        
        # Display manager signals
        self.display_manager.contentChanged.connect(self._update_display)
        self.display_manager.errorOccurred.connect(self._show_error)
        
    def _handle_view_change(self, view: str):
        """Handle view mode changes"""
        if view == "Favorites":
            self.display_manager.display_favorites()
        elif view == "Recent":
            self.display_manager.display_recent()
        else:
            self.display_manager.display_folder_contents(None)  # Root folder
            
    def _handle_search(self, text: str):
        """Handle search input"""
        if text:
            self.display_manager.search_content(text)
        else:
            self._handle_view_change(self.view_mode.currentText())
            
    def _handle_category_select(self, item: QTreeWidgetItem):
        """Handle category selection"""
        folder_id = item.data(0, Qt.UserRole)
        if folder_id:
            self.display_manager.navigate_to_folder(folder_id)
            
    def _handle_item_select(self, item: QListWidgetItem):
        """Handle item selection"""
        data = item.data(Qt.UserRole)
        if data:
            self.itemSelected.emit(data)
            if data.get('mimeType', '').startswith('audio/'):
                self.audio_player.load_file(data.get('webContentLink'))
                self.lyrics_viewer.load_lyrics(data.get('id'))
                
    def _update_display(self, content: Dict):
        """Update display with new content"""
        self.content_list.clear()
        
        for item in content.get('data', []):
            list_item = QListWidgetItem(item.get('name', ''))
            list_item.setData(Qt.UserRole, item)
            
            # Set icon based on type
            if item.get('mimeType') == 'application/vnd.google-apps.folder':
                list_item.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
            elif item.get('mimeType', '').startswith('audio/'):
                list_item.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
                
            self.content_list.addItem(list_item)
            
    def _show_error(self, message: str):
        """Show error message"""
        QMessageBox.critical(self, "Error", message)

# Singleton instance
display_manager = DisplayManager()