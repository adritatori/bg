from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
from datetime import datetime

from flask import jsonify
import obspy
from app.core.data_loader import (
    get_dataset_files, get_datasets, get_time_range, load_data,
    generate_metadata, check_data_integrity, get_available_date_ranges,
    print_file_dates
)
from app.core.processing import get_denoising_methods, get_method_parameters, get_raw_data_from_files, process_data, detect_events
from app.models.schemas import (
    DatasetFiles, DatasetInfo, FileInfo, ProcessingRequest, PerformanceMetrics,
    EventDetectionRequest, DetectedEvent, TimeSeriesData, ComparisonData,
    AvailableDates
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/datasets", response_model=List[DatasetInfo])
async def datasets():
    """Get available datasets."""
    return [DatasetInfo(name=name, description=f"Seismic data for {name}") for name in get_datasets()]

@router.get("/datasets/{dataset}/timerange")
async def timerange(dataset: str):
    """Get time range for a specific dataset."""
    try:
        start, end = get_time_range(dataset)
        return {"start_time": start.isoformat(), "end_time": end.isoformat()}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{dataset}/{file}")
async def get_mseed_data(dataset: str, file: str):
    try:
        data = await get_raw_data_from_files(dataset, file)
        return data
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


# @router.get("/datasets/{dataset}/available-dates", response_model=AvailableDates)
# async def available_dates(dataset: str):
#     """Get available dates for a specific dataset."""
#     try:
#         dates = get_available_date_ranges(dataset)
#         return AvailableDates(dates=dates)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@router.get("/processing-methods", response_model=Dict[str, Dict[str, Any]])
async def processing_methods():
    """Get available processing methods and their parameters."""
    methods = get_denoising_methods()
    return {method: get_method_parameters(method) for method in methods}

# @router.post("/process", response_model=PerformanceMetrics)
# async def process(request: ProcessingRequest):
#     """Process data with selected method and parameters."""
#     try:
#         if not check_data_availability(request.dataset, request.start_time, request.end_time):
#             raise HTTPException(status_code=404, detail="No data available for the specified time range")
        
#         data = load_data(request.dataset, request.start_time, request.end_time)
#         if data is None:
#             raise HTTPException(status_code=404, detail="No data found for the specified time range")
        
#         result = await process_data(data, request.method, request.parameters)
#         return PerformanceMetrics(**result)
#     except Exception as e:
#         logger.error(f"Error in process endpoint: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))

# @router.post("/detect-events", response_model=List[DetectedEvent])
# async def detect_events_endpoint(request: EventDetectionRequest):
#     """Detect seismic events in the data."""
#     try:
#         if not check_data_availability(request.dataset, request.start_time, request.end_time):
#             raise HTTPException(status_code=404, detail="No data available for the specified time range")
        
#         data = load_data(request.dataset, request.start_time, request.end_time)
#         if data is None:
#             raise HTTPException(status_code=404, detail="No data found for the specified time range")
        
#         events = await detect_events(data, request.method, request.parameters)
#         return events
#     except Exception as e:
#         logger.error(f"Error in detect_events endpoint: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))


@router.get("/{dataset}/files", response_model=DatasetFiles)
async def dataset_files(dataset: str):
    """Get files and their time ranges for a specific dataset."""
    try:
        files = get_dataset_files(dataset)
        return DatasetFiles(files=[FileInfo(**file) for file in files])
    except Exception as e:
        logger.error(f"Error getting files for {dataset}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting files: {str(e)}")
# @router.post("/check-integrity/{dataset}")
# async def check_integrity(dataset: str):
#     """Check the integrity of a dataset."""
#     try:
#         check_data_integrity(dataset)
#         return {"message": f"Integrity check completed for {dataset}"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.post("/generate-metadata/{dataset}")
# async def generate_metadata_endpoint(dataset: str):
#     """Generate metadata for a dataset and store in the database."""
#     try:
#         generate_metadata(dataset)
#         return {"message": f"Metadata generated for {dataset}"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@router.get("/print-file-dates/{dataset}")
async def print_file_dates_endpoint(dataset: str):
    """Print start and end dates for each file in a dataset."""
    try:
        print_file_dates(dataset)
        return {"message": f"File dates printed for {dataset}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))