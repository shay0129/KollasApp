"""Services configuration"""

GOOGLE_DRIVE_CONFIG = {
    # Cache settings
    'CACHE_MAX_SIZE': 1024 * 1024 * 1024,  # 1GB
    'CACHE_DIR': 'data/cache',
    'CACHE_CLEANUP_INTERVAL': 24,  # hours
    
    # Sync settings
    'SYNC_INTERVAL': 300,  # 5 minutes
    'MAX_RESULTS_PER_PAGE': 1000,
    
    # File structure
    'ROOT_FOLDER_NAME': 'KollasApp',
    'FOLDER_STRUCTURE': {
        'piyyutim': {
            'daily': {},
            'shabbat': {},
            'holidays': {
                'rosh_hashana': {},
                'yom_kippur': {},
                'sukkot': {},
                'pesach': {},
                'shavuot': {}
            }
        },
        'learning_materials': {},
        'recordings': {
            'original': {},
            'user_practice': {}
        }
    }
}

DOWNLOAD_CONFIG = {
    'CHUNK_SIZE': 8192,
    'TIMEOUT': 30,
    'MAX_RETRIES': 3,
    'CACHE_DIR': 'data/temp',
    'FILE_TYPES': {
        'AUDIO': ['audio/mpeg', 'audio/wav', 'audio/ogg'],
        'DOCUMENT': ['application/pdf', 'application/msword', 'text/plain'],
        'IMAGE': ['image/jpeg', 'image/png', 'image/svg+xml']
    }
}

# Error messages
ERROR_MESSAGES = {
    'CREDENTIALS_NOT_FOUND': 'Google Drive credentials file not found',
    'SERVICE_INIT_FAILED': 'Failed to initialize Google Drive service',
    'DOWNLOAD_FAILED': 'Failed to download file',
    'CACHE_ERROR': 'Error managing cache',
    'NETWORK_ERROR': 'Network connection error'
}