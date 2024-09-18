import os
import numpy as np
from obspy import Stream, read
from typing import Dict, Any, List
from app.core.data_loader import DATA_DIR
from app.models.schemas import DetectedEvent
from datetime import datetime

def get_denoising_methods():
    """Return available de-noising methods."""
    return ["bandpass", "lowpass", "highpass", "moving_average"]

async def get_raw_data_from_files(dataset: str, file: str) -> Dict[str, Any]:
    """
    Fetch raw data from a specified file within a dataset.
    
    :param dataset: Name of the dataset
    :param file: Name of the file
    :return: Dictionary containing metadata and trace data
    """
    file_path = os.path.join(DATA_DIR, dataset, file)
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found on disk: {file_path}")
    
    try:
        st = read(file_path)
    except Exception as e:
        raise ValueError(f"Error reading file: {str(e)}")
    
    if len(st) == 0:
        raise ValueError("No data found in the file")
    
    data = {
        "metadata": {
            "dataset": dataset,
            "filename": file,
            "start_time": str(st[0].stats.starttime),
            "end_time": str(st[0].stats.endtime),
            "sampling_rate": st[0].stats.sampling_rate
        },
        "traces": []
    }
    
    for tr in st:
        trace_data = {
            "channel": tr.stats.channel,
            "time": tr.times().tolist(),
            "amplitude": tr.data.tolist()
        }
        data["traces"].append(trace_data)
    
    return data

def get_method_parameters(method: str) -> Dict[str, Any]:
    """Return parameters for a given de-noising method."""
    params = {
        "bandpass": {
            "freqmin": {"type": "float", "min": 0.1, "max": 25, "default": 1},
            "freqmax": {"type": "float", "min": 0.1, "max": 25, "default": 10},
        },
        "lowpass": {
            "freq": {"type": "float", "min": 0.1, "max": 25, "default": 1},
        },
        "highpass": {
            "freq": {"type": "float", "min": 0.1, "max": 25, "default": 1},
        },
        "moving_average": {
            "window_size": {"type": "int", "min": 1, "max": 1000, "default": 10},
        }
    }
    return params.get(method, {})

async def process_data(data: Stream, method: str, parameters: Dict[str, Any]) -> Dict[str, float]:
    """Process seismic data using the specified method and parameters."""
    if not data or len(data) == 0:
        raise ValueError("No data found for the specified time range")

    snr_before = calculate_snr(data)
    
    if method == "bandpass":
        processed_data = data.copy().filter('bandpass', freqmin=parameters['freqmin'], freqmax=parameters['freqmax'])
    elif method == "lowpass":
        processed_data = data.copy().filter('lowpass', freq=parameters['freq'])
    elif method == "highpass":
        processed_data = data.copy().filter('highpass', freq=parameters['freq'])
    elif method == "moving_average":
        processed_data = Stream([tr.copy() for tr in data])
        for tr in processed_data:
            tr.data = np.convolve(tr.data, np.ones(parameters['window_size']), 'same') / parameters['window_size']
    else:
        raise ValueError(f"Unknown processing method: {method}")

    snr_after = calculate_snr(processed_data)
    improvement = (snr_after - snr_before) / snr_before * 100 if snr_before != 0 else 0

    return {
        "snr_before": snr_before,
        "snr_after": snr_after,
        "improvement": improvement
    }

def calculate_snr(data: Stream) -> float:
    """Calculate Signal-to-Noise Ratio of the data."""
    if not data or len(data) == 0:
        return 0
    signal = np.concatenate([tr.data for tr in data])
    return np.mean(np.abs(signal)) / np.std(signal) if len(signal) > 0 else 0

async def detect_events(data: Stream, method: str, parameters: Dict[str, Any]) -> List[DetectedEvent]:
    """Detect seismic events in the data."""
    if method == "sta_lta":
        from obspy.signal.trigger import recursive_sta_lta, trigger_onset
        
        sta = parameters.get('sta', 1)
        lta = parameters.get('lta', 10)
        threshold = parameters.get('threshold', 3)
        
        events = []
        for tr in data:
            cft = recursive_sta_lta(tr.data, int(sta * tr.stats.sampling_rate), int(lta * tr.stats.sampling_rate))
            triggers = trigger_onset(cft, threshold, threshold)
            
            for on, off in triggers:
                start_time = tr.stats.starttime + on / tr.stats.sampling_rate
                end_time = tr.stats.starttime + off / tr.stats.sampling_rate
                magnitude = np.max(np.abs(tr.data[on:off]))
                confidence = cft[on]
                
                events.append(DetectedEvent(
                    start_time=start_time.datetime,
                    end_time=end_time.datetime,
                    magnitude=float(magnitude),
                    confidence=float(confidence)
                ))
        
        return events
    else:
        raise ValueError(f"Unknown event detection method: {method}")