import os
from obspy import Stream, read
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.core.database import insert_file_metadata, get_dataset_timerange, get_files_in_timerange, init_db
import numpy as np

DATA_DIR = "data"
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_datasets():
    """Return available datasets (lunar and mars)."""
    datasets = [d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))]
    if not datasets:
        logger.warning("No datasets found in the data directory.")
    return datasets

def get_time_range(dataset):
    """Get time range for a dataset."""
    data_path = os.path.join(DATA_DIR, dataset)
    start_time = None
    end_time = None
    for file in os.listdir(data_path):
        if file.endswith('.mseed'):
            st = read(os.path.join(data_path, file))
            if start_time is None or st[0].stats.starttime < start_time:
                start_time = st[0].stats.starttime
            if end_time is None or st[0].stats.endtime > end_time:
                end_time = st[0].stats.endtime
    return start_time, end_time

def load_data(dataset, start_time, end_time):
    """Load data from mseed files within the specified time range."""
    data_path = os.path.join(DATA_DIR, dataset, "data")
    st = Stream()
    
    for file in os.listdir(data_path):
        if file.endswith('.mseed'):
            try:
                file_st = read(os.path.join(data_path, file))
                for tr in file_st:
                    if tr.stats.starttime <= end_time and tr.stats.endtime >= start_time:
                        st += tr
            except Exception as e:
                logger.error(f"Error reading file {file}: {str(e)}")
    
    if len(st) == 0:
        logger.warning(f"No data found for the specified time range in dataset {dataset}")
        return None
    
    return st

def process_file(file_path, dataset):
    """Process a single file and return its metadata."""
    try:
        st = read(file_path)
        metadata = []
        for tr in st:
            metadata.append({
                'dataset': dataset,
                'filename': os.path.basename(file_path),
                'start_time': tr.stats.starttime.datetime,
                'end_time': tr.stats.endtime.datetime,
                'sampling_rate': tr.stats.sampling_rate
            })
        return metadata
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {str(e)}")
        return []

def generate_metadata(dataset):
    """Generate metadata for a dataset and store in the database."""
    init_db()  # Ensure the database is initialized
    data_path = os.path.join(DATA_DIR, dataset)
    
    if not os.path.exists(data_path):
        logger.error(f"Data path does not exist: {data_path}")
        raise FileNotFoundError(f"Data path does not exist: {data_path}")
    
    files = [f for f in os.listdir(data_path) if f.endswith('.mseed')]
    
    if not files:
        logger.warning(f"No .mseed files found in {data_path}")
        return
    
    with ThreadPoolExecutor() as executor:
        future_to_file = {executor.submit(process_file, os.path.join(data_path, f), dataset): f for f in files}
        for future in as_completed(future_to_file):
            file = future_to_file[future]
            try:
                metadata = future.result()
                for item in metadata:
                    insert_file_metadata(**item)
            except Exception as e:
                logger.error(f"Error processing file {file}: {str(e)}")
    
    logger.info(f"Metadata generation completed for {dataset}")

def get_dataset_files(dataset):
    """Get files and their time ranges for a dataset."""
    data_path = os.path.join(DATA_DIR, dataset)
    files_info = []
    
    logger.info(f"Searching for .mseed files in {data_path}")
    
    for file in os.listdir(data_path):
        if file.endswith('.mseed'):
            logger.info(f"Processing file: {file}")
            try:
                st = read(os.path.join(data_path, file))
                start_time = min(tr.stats.starttime for tr in st)
                end_time = max(tr.stats.endtime for tr in st)
                files_info.append({
                    "filename": file,
                    "start_time": start_time.datetime,
                    "end_time": end_time.datetime
                })
                logger.info(f"Added file: {file}, Start: {start_time}, End: {end_time}")
            except Exception as e:
                logger.error(f"Error processing file {file}: {str(e)}")
    
    logger.info(f"Found {len(files_info)} files")
    return sorted(files_info, key=lambda x: x['start_time'])

def get_available_date_ranges(dataset):
    """Get available dates for a dataset."""
    data_path = os.path.join(DATA_DIR, dataset)
    available_dates = []

    try:
        for file in os.listdir(data_path):
            if file.endswith('.mseed'):
                st = read(os.path.join(data_path, file))
                for tr in st:
                    available_dates.append({
                        "Start": tr.stats.starttime,
                        "End": tr.stats.endtime
                    })
    except Exception as e:
        print(f"Error processing file {file}: {e}")

    return sorted(available_dates, key=lambda x: x['Start'])  # Remove duplicates and sort

def check_data_integrity(dataset):
    """Check the integrity of all mseed files in a dataset."""
    data_path = os.path.join(DATA_DIR, dataset)
    
    for file in os.listdir(data_path):
        if file.endswith('.mseed'):
            try:
                st = read(os.path.join(data_path, file))
                if len(st) == 0:
                    logger.warning(f"File {file} in {dataset} contains no traces")
                for tr in st:
                    if np.isnan(tr.data).any():
                        logger.warning(f"File {file} in {dataset} contains NaN values")
                    if not np.isfinite(tr.data).all():
                        logger.warning(f"File {file} in {dataset} contains infinite values")
            except Exception as e:
                logger.error(f"Error reading file {file} in {dataset}: {str(e)}")
    
    logger.info(f"Completed integrity check for {dataset}")

def print_file_dates(dataset):
    data_path = os.path.join(DATA_DIR, dataset)
    for file in os.listdir(data_path):
        if file.endswith('.mseed'):
            st = read(os.path.join(data_path, file))
            print(f"File: {file}")
            for tr in st:
                print(f"  Start: {tr.stats.starttime}, End: {tr.stats.endtime}")