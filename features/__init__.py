"""
Additional features module for KollasApp
Contains achievements system and community forum
"""

from .achievements_system import AchievementsManager
from .community_forum import CommunityManager

__all__ = ['AchievementsManager', 'CommunityManager']