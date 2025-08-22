# Sentinel Hub Integration Guide

## Overview

SatChat now includes advanced Sentinel Hub API integration for powerful satellite data processing and marine debris detection. This document explains how to use the new features.

## Key Features

### 1. Process API
- Real-time satellite image processing
- Custom evalscripts for marine debris detection
- Multi-band analysis (RGB, NIR, SWIR)
- Cloud-optimized processing

### 2. Statistical API
- Time-series analysis of debris accumulation
- Water quality metrics
- Aggregated statistics (daily, weekly, monthly)
- Trend detection and anomaly analysis

### 3. Batch Processing API
- Large-scale processing for entire Korean waters
- Automated scheduling and monitoring
- Cloud-optimized GeoTIFF outputs
- S3 integration for results storage

## Marine Debris Detection Algorithm

### Spectral Indices Used

1. **Floating Algae Index (FAI)**
   - Detects floating materials on water surface
   - Formula: `NIR - (RED + (SWIR2 - RED) * λ_ratio)`
   - Threshold: >0.02 indicates potential debris

2. **Normalized Difference Water Index (NDWI)**
   - Distinguishes water from non-water features
   - Formula: `(GREEN - NIR) / (GREEN + NIR)`
   - Threshold: <0.3 for debris detection

3. **Plastic Index (PI)**
   - Experimental index for plastic detection
   - Formula: `(NIR - RED) / (NIR + RED) * (SWIR1 / SWIR2)`
   - Threshold: >0.1 indicates plastic materials

4. **Floating Debris Index (FDI)**
   - Custom composite index for marine debris
   - Formula: `FAI * 2 + PI`
   - Confidence levels:
     - High (>0.05): Definite debris (255)
     - Medium (>0.03): Probable debris (170)
     - Low (>0.01): Possible debris (85)

## API Endpoints

### Process Marine Debris
```http
POST /api/v1/sentinel-hub/process/marine-debris
```

Parameters:
- `bbox`: Bounding box [min_lon, min_lat, max_lon, max_lat]
- `start_date`: Start date for analysis
- `end_date`: End date (optional, defaults to now)
- `resolution`: Resolution in meters (10-100)
- `max_cloud`: Maximum cloud coverage % (0-100)

Example:
```bash
curl -X POST "http://localhost:8000/api/v1/sentinel-hub/process/marine-debris" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bbox": [124.0, 33.0, 127.0, 39.0],
    "start_date": "2024-01-01T00:00:00Z",
    "resolution": 10,
    "max_cloud": 20
  }'
```

### Get Statistics
```http
GET /api/v1/sentinel-hub/statistics/marine-debris
```

Parameters:
- `area`: Korean sea area (west_sea, south_sea, east_sea)
- `days_back`: Days to analyze (1-90)
- `aggregation`: Aggregation interval (P1D=daily, P1W=weekly)

Example:
```bash
curl "http://localhost:8000/api/v1/sentinel-hub/statistics/marine-debris?area=west_sea&days_back=7" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Create Batch Job
```http
POST /api/v1/sentinel-hub/batch/create
```

Parameters:
- `areas`: List of areas to process
- `days_back`: Days to analyze (1-90)

Example:
```bash
curl -X POST "http://localhost:8000/api/v1/sentinel-hub/batch/create" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "areas": ["west_sea", "south_sea", "east_sea"],
    "days_back": 30
  }'
```

### Monitor Batch Job
```http
GET /api/v1/sentinel-hub/batch/{job_id}/status
```

### Process All Korean Waters
```http
POST /api/v1/sentinel-hub/process/korean-waters
```

Parameters:
- `days_back`: Days to analyze (1-30)
- `resolution`: Resolution in meters (10-100)

## Setup Instructions

### 1. Get Sentinel Hub Account

1. Sign up at [Sentinel Hub](https://www.sentinel-hub.com/)
2. Create a new configuration
3. Note your Instance ID
4. Create OAuth client credentials

### 2. Configure Environment Variables

Add to your `.env` file:
```env
# Sentinel Hub API
SENTINEL_HUB_CLIENT_ID=your-client-id
SENTINEL_HUB_CLIENT_SECRET=your-client-secret
SENTINEL_HUB_INSTANCE_ID=your-instance-id
```

### 3. Test the Integration

```python
# Test script
import asyncio
from satchat.services.satellite.sentinel_hub import SentinelHubService

async def test_sentinel_hub():
    service = SentinelHubService()
    
    # Test authentication
    token = await service.get_access_token()
    print(f"Token obtained: {token[:20]}...")
    
    # Test processing
    results = await service.process_korean_waters(days_back=1)
    print(f"Processing results: {results}")

asyncio.run(test_sentinel_hub())
```

## Korean Sea Areas

### West Sea (서해)
- **Bbox**: [124.0, 33.0, 127.0, 39.0]
- **Characteristics**: High turbidity, shallow waters
- **Challenges**: Sediment interference, tidal variations
- **Optimizations**: Enhanced sediment filtering, tidal correction

### South Sea (남해)
- **Bbox**: [126.0, 32.0, 130.0, 35.0]
- **Characteristics**: Clear waters, island chains
- **Challenges**: Island shadows, aquaculture interference
- **Optimizations**: Island masking, aquaculture detection

### East Sea (동해)
- **Bbox**: [128.0, 35.0, 132.0, 38.5]
- **Characteristics**: Deep waters, strong currents
- **Challenges**: Wave effects, seasonal variations
- **Optimizations**: Wave correction, seasonal adjustments

## Performance Optimization

### Caching Strategy
- OAuth tokens cached for session duration
- Processing results cached in S3
- Statistical data cached in Redis

### Batch Processing
- Use batch API for areas >100 km²
- Schedule during off-peak hours
- Monitor job status asynchronously

### Resolution Guidelines
- 10m: Detailed debris detection
- 20m: Standard monitoring
- 60m: Quick overview scans
- 100m: Large area statistics

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify client credentials
   - Check instance ID
   - Ensure account has active subscription

2. **Processing Timeouts**
   - Reduce area size
   - Increase resolution (lower detail)
   - Use batch processing for large areas

3. **No Data Available**
   - Check date range
   - Verify area coordinates
   - Consider cloud coverage settings

4. **Rate Limiting**
   - Implement exponential backoff
   - Use batch processing
   - Cache results aggressively

## Advanced Features

### Custom Evalscripts

Modify the evalscript in `sentinel_hub.py` to adjust detection parameters:

```javascript
// Adjust thresholds for your specific needs
if (FDI > 0.05 && FAI > 0.02 && NDWI < 0.3) {
    is_debris = 255;  // High confidence
}
```

### Multi-temporal Analysis

Combine multiple time periods for trend detection:

```python
# Analyze debris accumulation over time
for month in range(1, 13):
    stats = await service.get_statistics(
        geometry=area,
        time_range=(start_of_month, end_of_month),
        aggregation_interval="P1D"
    )
```

### Export Options

- **GeoTIFF**: Full resolution imagery
- **PNG**: Visualization outputs
- **JSON**: Statistical data
- **NetCDF**: Time-series data

## Best Practices

1. **Always use appropriate resolution**
   - Balance between detail and processing time
   - Consider your analysis needs

2. **Implement proper error handling**
   - Retry failed requests
   - Log all errors for debugging

3. **Monitor usage and costs**
   - Track API calls
   - Optimize processing areas

4. **Validate results**
   - Cross-reference with ground truth
   - Adjust thresholds based on validation

## Support

For issues or questions:
- Email: dev@telefix.co.kr
- GitHub Issues: https://github.com/djyalu/sat_chat/issues
- Sentinel Hub Forum: https://forum.sentinel-hub.com/