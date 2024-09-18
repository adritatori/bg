# import os

# class Config:
#     # Database configuration
#     DATABASE_FILE = os.getenv('DATABASE_FILE', 'seismic_metadata.db')
    
#     # Data directory configuration
#     DATA_DIR = os.getenv('DATA_DIR', 'data')
    
#     # API configuration
#     API_HOST = os.getenv('API_HOST', '0.0.0.0')
#     API_PORT = int(os.getenv('API_PORT', 8000))
    
#     # Processing parameters
#     DEFAULT_FREQMIN = float(os.getenv('DEFAULT_FREQMIN', 1.0))
#     DEFAULT_FREQMAX = float(os.getenv('DEFAULT_FREQMAX', 10.0))

# config = Config()