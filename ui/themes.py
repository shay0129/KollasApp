from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtCore import Qt
import json
import logging
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class ThemeColors:
    """הגדרת צבעים לערכת נושא"""
    primary: str = "#2E4057"
    secondary: str = "#4F5D75"
    background: str = "#FFFFFF"
    text: str = "#333333"
    accent: str = "#7C98B3"
    error: str = "#FF6B6B"
    success: str = "#4ECB71"
    warning: str = "#FFB347"
    disabled: str = "#CCCCCC"
    hover: str = "#E8EFF5"

@dataclass
class ThemeFonts:
    """הגדרת גופנים לערכת נושא"""
    family: str = "Arial"
    size_small: int = 10
    size_normal: int = 12
    size_large: int = 14
    size_xlarge: int = 18
    weight_normal: int = 400
    weight_bold: int = 700

class StyleManager:
    def __init__(self):
        """אתחול מנהל העיצוב"""
        self.current_theme = "light"
        self.themes_dir = Path("resources/themes")
        self.themes_dir.mkdir(parents=True, exist_ok=True)
        self._load_themes()
        
    def _load_themes(self):
        """טעינת ערכות נושא מקבצי JSON"""
        self.themes = {
            "light": self._create_light_theme(),
            "dark": self._create_dark_theme(),
            "sepia": self._create_sepia_theme(),
            "traditional": self._create_traditional_theme()
        }
        
        # טעינת ערכות נושא מותאמות אישית
        for theme_file in self.themes_dir.glob("*.json"):
            try:
                with open(theme_file, 'r', encoding='utf-8') as f:
                    theme_data = json.load(f)
                    self.themes[theme_file.stem] = theme_data
            except Exception as e:
                logging.error(f"Error loading theme {theme_file}: {e}")

    def _create_light_theme(self) -> Dict:
        """יצירת ערכת נושא בהירה"""
        return {
            "colors": ThemeColors(
                primary="#2E4057",
                secondary="#4F5D75",
                background="#FFFFFF",
                text="#333333",
                accent="#7C98B3"
            ),
            "fonts": ThemeFonts(
                family="Arial",
                size_normal=12,
                weight_normal=400
            ),
            "styles": {
                "QMainWindow": """
                    QMainWindow {
                        background-color: #FFFFFF;
                    }
                """,
                "QWidget": """
                    QWidget {
                        background-color: #FFFFFF;
                        color: #333333;
                        font-family: Arial;
                    }
                """,
                "QPushButton": """
                    QPushButton {
                        background-color: #2E4057;
                        color: white;
                        border: none;
                        padding: 5px 15px;
                        border-radius: 3px;
                    }
                    QPushButton:hover {
                        background-color: #4F5D75;
                    }
                    QPushButton:disabled {
                        background-color: #CCCCCC;
                    }
                """,
                "QLineEdit": """
                    QLineEdit {
                        padding: 5px;
                        border: 1px solid #CCCCCC;
                        border-radius: 3px;
                        background-color: white;
                    }
                    QLineEdit:focus {
                        border: 1px solid #7C98B3;
                    }
                """
            }
        }

    def _create_dark_theme(self) -> Dict:
        """יצירת ערכת נושא כהה"""
        return {
            "colors": ThemeColors(
                primary="#BB86FC",
                secondary="#03DAC6",
                background="#121212",
                text="#FFFFFF",
                accent="#3700B3"
            ),
            "fonts": ThemeFonts(),
            "styles": {
                "QMainWindow": """
                    QMainWindow {
                        background-color: #121212;
                    }
                """,
                "QWidget": """
                    QWidget {
                        background-color: #121212;
                        color: white;
                    }
                """,
                "QPushButton": """
                    QPushButton {
                        background-color: #BB86FC;
                        color: black;
                        border: none;
                        padding: 5px 15px;
                        border-radius: 3px;
                    }
                    QPushButton:hover {
                        background-color: #3700B3;
                        color: white;
                    }
                """
            }
        }

    def _create_sepia_theme(self) -> Dict:
        """יצירת ערכת נושא ספיה"""
        return {
            "colors": ThemeColors(
                primary="#704214",
                secondary="#8B4513",
                background="#FFF8DC",
                text="#463E3F",
                accent="#B8860B"
            ),
            "fonts": ThemeFonts(
                family="Times New Roman",
                size_normal=14
            ),
            "styles": {
                "QMainWindow": """
                    QMainWindow {
                        background-color: #FFF8DC;
                    }
                """,
                "QWidget": """
                    QWidget {
                        background-color: #FFF8DC;
                        color: #463E3F;
                        font-family: "Times New Roman";
                    }
                """
            }
        }

    def _create_traditional_theme(self) -> Dict:
        """יצירת ערכת נושא מסורתית"""
        return {
            "colors": ThemeColors(
                primary="#8B4513",
                secondary="#DAA520",
                background="#F5DEB3",
                text="#000000",
                accent="#CD853F"
            ),
            "fonts": ThemeFonts(
                family="David CLM",
                size_normal=14,
                size_large=18
            ),
            "styles": {
                "QMainWindow": """
                    QMainWindow {
                        background-color: #F5DEB3;
                    }
                """,
                "QWidget": """
                    QWidget {
                        background-color: #F5DEB3;
                        color: black;
                        font-family: "David CLM";
                    }
                """
            }
        }

    def apply_theme(self, widget: QWidget, theme_name: str = None):
        """החלת ערכת נושא על widget"""
        theme_name = theme_name or self.current_theme
        if theme_name not in self.themes:
            logging.error(f"Theme {theme_name} not found")
            return
            
        theme = self.themes[theme_name]
        
        # החלת סגנון בסיסי
        widget.setStyleSheet(theme["styles"].get("QWidget", ""))
        
        # החלת צבעים וגופנים
        palette = widget.palette()
        colors = theme["colors"]
        fonts = theme["fonts"]
        
        # עדכון צבעים בפלטה
        palette.setColor(QPalette.Window, QColor(colors.background))
        palette.setColor(QPalette.WindowText, QColor(colors.text))
        palette.setColor(QPalette.Base, QColor(colors.background))
        palette.setColor(QPalette.AlternateBase, QColor(colors.hover))
        palette.setColor(QPalette.Text, QColor(colors.text))
        palette.setColor(QPalette.Button, QColor(colors.primary))
        palette.setColor(QPalette.ButtonText, QColor("#FFFFFF"))
        palette.setColor(QPalette.Highlight, QColor(colors.accent))
        palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
        
        widget.setPalette(palette)
        
        # החלת גופן
        font = QFont(fonts.family, fonts.size_normal)
        widget.setFont(font)
        
        # החלת סגנונות ספציפיים לכל רכיב
        style_sheet = ""
        for widget_type, style in theme["styles"].items():
            style_sheet += f"{widget_type} {style}\n"
        widget.setStyleSheet(style_sheet)

    def create_custom_theme(self, name: str, colors: Dict, fonts: Dict, styles: Dict):
        """יצירת ערכת נושא מותאמת אישית"""
        theme_data = {
            "colors": ThemeColors(**colors),
            "fonts": ThemeFonts(**fonts),
            "styles": styles
        }
        
        # שמירה לקובץ
        theme_file = self.themes_dir / f"{name}.json"
        try:
            with open(theme_file, 'w', encoding='utf-8') as f:
                json.dump(theme_data, f, ensure_ascii=False, indent=2)
            self.themes[name] = theme_data
            logging.info(f"Created custom theme: {name}")
        except Exception as e:
            logging.error(f"Error creating custom theme: {e}")

    def get_available_themes(self) -> list:
        """קבלת רשימת ערכות נושא זמינות"""
        return list(self.themes.keys())

    def get_theme_colors(self, theme_name: str = None) -> Optional[ThemeColors]:
        """קבלת צבעי ערכת נושא"""
        theme_name = theme_name or self.current_theme
        if theme_name in self.themes:
            return self.themes[theme_name]["colors"]
        return None

    def get_theme_fonts(self, theme_name: str = None) -> Optional[ThemeFonts]:
        """קבלת גופני ערכת נושא"""
        theme_name = theme_name or self.current_theme
        if theme_name in self.themes:
            return self.themes[theme_name]["fonts"]
        return None

# יצירת singleton
style_manager = StyleManager()