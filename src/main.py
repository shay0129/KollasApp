from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sqlite3
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict
import sys

from services.google_services import drive_service
from managers.audio_processor import AudioProcessor
from managers.content_manager import ContentManager
from core.db import DatabaseManager
from ui.custom_widgets import BookPage, AudioPlayer, LyricsViewer
from ui.themes import StyleManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_services()
        self.init_ui()
        self.load_settings()
        
    def init_services(self):
        """Initialize all required services"""
        try:
            self.db = DatabaseManager()
            self.content_manager = ContentManager()
            self.audio_processor = AudioProcessor()
            self.style_manager = StyleManager()
            logging.info("Services initialized successfully")
        except Exception as e:
            logging.error(f"Error initializing services: {e}")
            QMessageBox.critical(self, "שגיאה", "שגיאה באתחול המערכת")
            sys.exit(1)

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle('פיוטי קהילת קוצ\'ין - שימור המסורת')
        self.setGeometry(100, 100, 1200, 800)
        self.setLayoutDirection(Qt.RightToLeft)
        
        # Set theme
        self.style_manager.apply_theme(self)
        
        # Main layout with toolbar and book
        main_layout = QVBoxLayout()
        
        # Toolbar
        toolbar = self.create_toolbar()
        main_layout.addWidget(toolbar)
        
        # Book widget
        self.book_widget = QWidget()
        book_layout = QHBoxLayout()
        
        # Right page (Navigation and Piyyut List)
        self.right_page = BookPage()
        self.setup_right_page()
        book_layout.addWidget(self.right_page)
        
        # Left page (Lyrics and Controls)
        self.left_page = BookPage()
        self.setup_left_page()
        book_layout.addWidget(self.left_page)
        
        self.book_widget.setLayout(book_layout)
        main_layout.addWidget(self.book_widget)
        
        # Central widget
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # Status bar
        self.statusBar().showMessage('מוכן')

    def create_toolbar(self) -> QToolBar:
        """Create main toolbar"""
        toolbar = QToolBar()
        
        # Search
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("חיפוש...")
        self.search_box.textChanged.connect(self.filter_piyyutim)
        toolbar.addWidget(self.search_box)
        
        # View options
        view_menu = QComboBox()
        view_menu.addItems(["הכל", "מועדפים", "היסטוריה", "לפי חג", "לפי נושא"])
        view_menu.currentTextChanged.connect(self.change_view)
        toolbar.addWidget(view_menu)
        
        # Settings
        settings_btn = QPushButton("הגדרות")
        settings_btn.clicked.connect(self.show_settings)
        toolbar.addWidget(settings_btn)
        
        return toolbar

    def setup_right_page(self):
        """Setup the right page with navigation and piyyut list"""
        layout = QVBoxLayout()
        
        # Categories tree
        self.categories_tree = QTreeWidget()
        self.categories_tree.setHeaderLabel("קטגוריות")
        self.load_categories()
        layout.addWidget(self.categories_tree)
        
        # Piyyut list
        self.piyyut_list = QListWidget()
        self.piyyut_list.itemClicked.connect(self.on_piyyut_selected)
        layout.addWidget(self.piyyut_list)
        
        self.right_page.setLayout(layout)

    def setup_left_page(self):
        """Setup the left page with lyrics and controls"""
        layout = QVBoxLayout()
        
        # Lyrics viewer
        self.lyrics_viewer = LyricsViewer()
        layout.addWidget(self.lyrics_viewer)
        
        # Audio player
        self.audio_player = AudioPlayer()
        layout.addWidget(self.audio_player)
        
        # Actions buttons
        actions_layout = QHBoxLayout()
        
        favorite_btn = QPushButton("הוסף למועדפים")
        favorite_btn.clicked.connect(self.toggle_favorite)
        actions_layout.addWidget(favorite_btn)
        
        share_btn = QPushButton("שתף")
        share_btn.clicked.connect(self.share_piyyut)
        actions_layout.addWidget(share_btn)
        
        layout.addLayout(actions_layout)
        
        # Notes section
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("הערות אישיות...")
        layout.addWidget(self.notes_edit)
        
        self.left_page.setLayout(layout)

    def load_categories(self):
        """Load piyyut categories into the tree"""
        try:
            categories = self.content_manager.get_categories()
            for category in categories:
                self.add_category_to_tree(category)
            logging.info("Categories loaded successfully")
        except Exception as e:
            logging.error(f"Error loading categories: {e}")
            self.show_error("שגיאה בטעינת הקטגוריות")

    def add_category_to_tree(self, category: Dict):
        """Add a category and its subcategories to the tree"""
        item = QTreeWidgetItem([category['name']])
        item.setData(0, Qt.UserRole, category['id'])
        
        if 'children' in category:
            for child in category['children']:
                child_item = self.add_category_to_tree(child)
                item.addChild(child_item)
                
        return item

    def on_piyyut_selected(self, item: QListWidgetItem):
        """Handle piyyut selection"""
        piyyut_id = item.data(Qt.UserRole)
        try:
            # Load piyyut data
            piyyut_data = self.content_manager.get_piyyut(piyyut_id)
            
            # Update lyrics
            self.lyrics_viewer.set_content(piyyut_data['lyrics'])
            
            # Load audio file
            self.audio_player.load_file(piyyut_data['audio_url'])
            
            # Load notes
            self.notes_edit.setText(
                self.db.get_user_notes('current_user', piyyut_id)
            )
            
            # Update history
            self.db.add_to_history('current_user', piyyut_id)
            
        except Exception as e:
            logging.error(f"Error loading piyyut: {e}")
            self.show_error("שגיאה בטעינת הפיוט")

    def filter_piyyutim(self, text: str):
        """Filter piyyutim list based on search text"""
        try:
            filtered_piyyutim = self.content_manager.search_piyyutim(text)
            self.update_piyyut_list(filtered_piyyutim)
        except Exception as e:
            logging.error(f"Error filtering piyyutim: {e}")

    def update_piyyut_list(self, piyyutim: List[Dict]):
        """Update the piyyut list with new data"""
        self.piyyut_list.clear()
        for piyyut in piyyutim:
            item = QListWidgetItem(piyyut['name'])
            item.setData(Qt.UserRole, piyyut['id'])
            self.piyyut_list.addItem(item)

    def toggle_favorite(self):
        """Toggle favorite status of current piyyut"""
        current_item = self.piyyut_list.currentItem()
        if current_item:
            piyyut_id = current_item.data(Qt.UserRole)
            try:
                is_favorite = self.db.toggle_favorite(
                    'current_user', piyyut_id
                )
                status = "הוסר" if not is_favorite else "נוסף"
                self.statusBar().showMessage(f"הפיוט {status} למועדפים")
            except Exception as e:
                logging.error(f"Error toggling favorite: {e}")
                self.show_error("שגיאה בעדכון מועדפים")

    def share_piyyut(self):
        """Share current piyyut"""
        current_item = self.piyyut_list.currentItem()
        if current_item:
            piyyut_id = current_item.data(Qt.UserRole)
            # Implement sharing functionality
            self.statusBar().showMessage("שיתוף פיוט - בפיתוח")

    def load_settings(self):
        """Load user settings"""
        try:
            settings = self.db.get_user_settings('current_user')
            self.apply_settings(settings)
        except Exception as e:
            logging.error(f"Error loading settings: {e}")

    def show_settings(self):
        """Show settings dialog"""
        # Implement settings dialog
        self.statusBar().showMessage("הגדרות - בפיתוח")

    def show_error(self, message: str):
        """Show error message to user"""
        QMessageBox.critical(self, "שגיאה", message)

    def closeEvent(self, event: QCloseEvent):
        """Handle application closing"""
        try:
            self.db.save_user_notes(
                'current_user',
                self.piyyut_list.currentItem().data(Qt.UserRole),
                self.notes_edit.toPlainText()
            )
            self.db.close()
            event.accept()
        except Exception as e:
            logging.error(f"Error closing application: {e}")
            event.accept()

def main():
    """Application entry point"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        app = QApplication(sys.argv)
        ex = MainWindow()
        ex.show()
        sys.exit(app.exec_())
    except Exception as e:
        logging.critical(f"Application failed to start: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()