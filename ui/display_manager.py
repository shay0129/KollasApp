from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import logging
from typing import Optional, List, Dict
from services.google_services import drive_service
from .custom_widgets import BookPage, SearchBar
from managers.audio_processor import AudioProcessor

class DisplayManager(QObject):
    """מנהל תצוגת התוכן"""
    
    contentChanged = pyqtSignal(dict)  # אות לשינוי תוכן
    errorOccurred = pyqtSignal(str)    # אות לשגיאה
    
    def __init__(self):
        super().__init__()
        self.current_path = []
        self.current_view = "all"  # all, favorites, recent, etc.
        self.audio_processor = AudioProcessor()
        
    def display_folder_contents(self, folder_id: str) -> List[Dict]:
        """הצגת תוכן תיקייה"""
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
            self.errorOccurred.emit(f"שגיאה בטעינת התיקייה: {str(e)}")
            return []
            
    def navigate_to_folder(self, folder_id: str):
        """מעבר לתיקייה"""
        self.current_path.append(folder_id)
        self.display_folder_contents(folder_id)
        
    def navigate_back(self):
        """חזרה לתיקייה הקודמת"""
        if self.current_path:
            self.current_path.pop()
            folder_id = self.current_path[-1] if self.current_path else None
            self.display_folder_contents(folder_id)

class ContentViewWidget(QWidget):
    """Widget להצגת תוכן"""
    
    itemSelected = pyqtSignal(dict)  # אות לבחירת פריט
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.display_manager = DisplayManager()
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        """הגדרת ממשק המשתמש"""
        layout = QVBoxLayout(self)
        
        # סרגל כלים עליון
        toolbar = QHBoxLayout()
        
        # כפתור חזרה
        self.back_btn = QPushButton("חזור")
        toolbar.addWidget(self.back_btn)
        
        # בחירת תצוגה
        self.view_mode = QComboBox()
        self.view_mode.addItems(["הכל", "מועדפים", "אחרונים"])
        toolbar.addWidget(self.view_mode)
        
        # חיפוש
        self.search_bar = SearchBar()
        toolbar.addWidget(self.search_bar)
        
        layout.addLayout(toolbar)
        
        # אזור התוכן המרכזי
        content_layout = QHBoxLayout()
        
        # עץ קטגוריות
        self.category_tree = QTreeWidget()
        self.category_tree.setHeaderLabel("קטגוריות")
        content_layout.addWidget(self.category_tree, 1)
        
        # רשימת פריטים
        self.content_list = QListWidget()
        content_layout.addWidget(self.content_list, 2)
        
        layout.addLayout(content_layout)
        
        # סרגל מצב
        self.status_bar = QStatusBar()
        layout.addWidget(self.status_bar)
        
    def _connect_signals(self):
        """חיבור אותות"""
        # חיבור אותות הניווט
        self.back_btn.clicked.connect(self.display_manager.navigate_back)
        self.view_mode.currentTextChanged.connect(self._handle_view_change)
        self.search_bar.searchRequested.connect(self._handle_search)
        
        # חיבור אותות התוכן
        self.category_tree.itemClicked.connect(self._handle_category_selected)
        self.content_list.itemClicked.connect(self._handle_item_selected)
        
        # חיבור אותות המנהל
        self.display_manager.contentChanged.connect(self._update_content_display)
        self.display_manager.errorOccurred.connect(self._show_error)
        
    def _handle_view_change(self, view_mode: str):
        """טיפול בשינוי מצב תצוגה"""
        self.display_manager.current_view = view_mode.lower()
        if view_mode == "מועדפים":
            self._load_favorites()
        elif view_mode == "אחרונים":
            self._load_recent()
        else:
            self._load_all()
            
    def _handle_search(self, query: str):
        """טיפול בחיפוש"""
        if query:
            self.display_manager.search_content(query)
        else:
            self._handle_view_change(self.view_mode.currentText())
            
    def _handle_category_selected(self, item: QTreeWidgetItem):
        """טיפול בבחירת קטגוריה"""
        category_id = item.data(0, Qt.UserRole)
        if category_id:
            self.display_manager.navigate_to_folder(category_id)
            
    def _handle_item_selected(self, item: QListWidgetItem):
        """טיפול בבחירת פריט"""
        item_data = item.data(Qt.UserRole)
        if item_data:
            self.itemSelected.emit(item_data)
            
    def _update_content_display(self, content_data: Dict):
        """עדכון תצוגת התוכן"""
        self.content_list.clear()
        
        # עדכון כותרת
        if 'type' in content_data:
            if content_data['type'] == 'search_results':
                self.status_bar.showMessage(f"תוצאות חיפוש: {content_data.get('query', '')}")
            elif content_data['type'] == 'folder_contents':
                path = ' > '.join(content_data.get('path', []))
                self.status_bar.showMessage(f"תיקייה: {path}")
        
        # הוספת פריטים לרשימה
        for item in content_data.get('data', []):
            list_item = QListWidgetItem(item.get('name', ''))
            list_item.setData(Qt.UserRole, item)
            
            # הוספת אייקון בהתאם לסוג הפריט
            if item.get('mimeType') == 'application/vnd.google-apps.folder':
                list_item.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
            elif item.get('mimeType', '').startswith('audio/'):
                list_item.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
                
            self.content_list.addItem(list_item)
            
    def _show_error(self, error_msg: str):
        """הצגת הודעת שגיאה"""
        QMessageBox.critical(self, "שגיאה", error_msg)
        self.status_bar.showMessage("אירעה שגיאה")
        
    def _load_favorites(self):
        """טעינת מועדפים"""
        pass  # יש להוסיף מימוש
        
    def _load_recent(self):
        """טעינת פריטים אחרונים"""
        pass  # יש להוסיף מימוש
        
    def _load_all(self):
        """טעינת כל הפריטים"""
        if self.display_manager.current_path:
            self.display_manager.display_folder_contents(self.display_manager.current_path[-1])
        else:
            self.display_manager.display_folder_contents(None)  # טעינת תיקיית השורש