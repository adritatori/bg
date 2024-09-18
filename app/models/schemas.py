from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class FileInfo(BaseModel):
    filename: str
    start_time: datetime
    end_time: datetime

class DatasetFiles(BaseModel):
    files: List[FileInfo]
    
class DatasetInfo(BaseModel):
    name: str
    description: str

class ProcessingRequest(BaseModel):
    dataset: str
    start_time: datetime
    end_time: datetime
    method: str
    parameters: Dict[str, Any]

class PerformanceMetrics(BaseModel):
    snr_before: float
    snr_after: float
    improvement: float

class EventDetectionRequest(BaseModel):
    dataset: str
    start_time: datetime
    end_time: datetime
    method: str
    parameters: Dict[str, Any]

class DetectedEvent(BaseModel):
    start_time: datetime
    end_time: datetime
    magnitude: float
    confidence: float

class TimeSeriesData(BaseModel):
    times: List[List[float]]
    values: List[List[float]]

class ComparisonData(BaseModel):
    raw: TimeSeriesData
    processed: TimeSeriesData

class AvailableDates(BaseModel):
    dates: List[str]