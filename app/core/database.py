import sqlite3
from datetime import datetime
import os

# Get the absolute path of the directory containing this file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Define the path to the instance folder
INSTANCE_DIR = os.path.join(os.path.dirname(BASE_DIR), 'instance')

# Ensure the instance directory exists
os.makedirs(INSTANCE_DIR, exist_ok=True)

# Define the database file path
DATABASE_FILE = os.path.join(INSTANCE_DIR, 'seismic_metadata.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS files
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     dataset TEXT NOT NULL,
                     filename TEXT NOT NULL,
                     start_time TEXT NOT NULL,
                     end_time TEXT NOT NULL,
                     sampling_rate REAL NOT NULL)''')
    conn.commit()
    conn.close()

def insert_file_metadata(dataset, filename, start_time, end_time, sampling_rate):
    conn = get_db_connection()
    conn.execute('INSERT INTO files (dataset, filename, start_time, end_time, sampling_rate) VALUES (?, ?, ?, ?, ?)',
                 (dataset, filename, start_time.isoformat(), end_time.isoformat(), sampling_rate))
    conn.commit()
    conn.close()

def get_dataset_timerange(dataset):
    conn = get_db_connection()
    result = conn.execute('SELECT MIN(start_time) as min_time, MAX(end_time) as max_time FROM files WHERE dataset = ?', (dataset,)).fetchone()
    conn.close()
    if result['min_time'] and result['max_time']:
        return datetime.fromisoformat(result['min_time']), datetime.fromisoformat(result['max_time'])
    return None, None

def get_files_in_timerange(dataset, start_time, end_time):
    conn = get_db_connection()
    result = conn.execute('''SELECT filename FROM files 
                             WHERE dataset = ? AND 
                             (start_time <= ? AND end_time >= ?)''', 
                          (dataset, end_time.isoformat(), start_time.isoformat())).fetchall()
    conn.close()
    return [row['filename'] for row in result]