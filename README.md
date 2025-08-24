# 🛰️ SatChat - Advanced Satellite Marine Debris Monitoring

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Sentinel-2](https://img.shields.io/badge/Sentinel--2-Active-brightgreen.svg)](https://sentinel.esa.int/web/sentinel/missions/sentinel-2)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Advanced marine debris detection and monitoring system using satellite imagery, machine learning, and multi-spectral analysis.**

🌐 **Live Demo**: [https://sat-chat.onrender.com](https://sat-chat.onrender.com)  
📊 **Dashboard**: [Multi-Analysis Dashboard](https://sat-chat.onrender.com/multi_analysis.html)

---

## ✨ Key Features

### 🛰️ Satellite Data Integration
- **Real-time Sentinel-2 data** from Copernicus program
- **Korean maritime focus** with optimized regional analysis
- **Multi-temporal data fusion** for enhanced accuracy
- **Cloud-free image selection** with quality filtering

### 🔬 Advanced Analysis Capabilities
- **Multi-Index Processing**: FDI, NDWI, MCI, Turbidity analysis
- **ML-Based Segmentation**: MARIDA 23-class Random Forest model
- **Spectral Enhancement**: Pan-sharpening and multi-temporal stacking
- **Field Validation System**: Ground-truth integration and confidence scoring

### 🗺️ Interactive Visualization
- **Real-time Interactive Maps** with Leaflet.js
- **Multi-layer Analysis** overlays and comparisons
- **Time-series Visualization** with Chart.js
- **Responsive Design** for desktop and mobile

### 🚀 Production-Ready Deployment
- **Render Cloud Platform** with automatic scaling
- **RESTful APIs** with comprehensive documentation
- **CORS-enabled** for cross-origin requests
- **Health monitoring** and status indicators

## 🏗️ System Architecture

```
🏠 SatChat System
├── 🚀 Production API (real_sentinel_api.py)
│   ├── Sentinel Hub integration
│   ├── Korean maritime regions
│   └── Health monitoring
│
├── 📊 Multi-Analysis Dashboard (multi_analysis.html)
│   ├── Interactive maps
│   ├── Real-time status
│   └── Analysis tools
│
├── 🔌 Specialized APIs (/apis/)
│   ├── Enhanced ML processing
│   ├── High-resolution analysis
│   ├── Free enhancement techniques
│   └── KOMPSAT integration
│
└── 🌐 Web Interface (/web/)
    ├── Landing pages
    └── Data visualization
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Sentinel Hub account ([Sign up here](https://www.sentinel-hub.com/))
- Git

### 1. Clone Repository
```bash
git clone https://github.com/djyalu/sat_chat.git
cd sat_chat
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit with your Sentinel Hub credentials
nano .env
```

**Required Environment Variables:**
```env
SENTINEL_HUB_CLIENT_ID=your_client_id
SENTINEL_HUB_CLIENT_SECRET=your_client_secret
```

### 4. Run Local Development Server
```bash
# Main API server
python real_sentinel_api.py

# Dashboard server (separate terminal)
python serve_dashboard.py
```

### 5. Access Applications
- **Main API**: http://localhost:8002
- **Dashboard**: http://localhost:5555
- **Interactive Analysis**: http://localhost:5555/multi_analysis.html

---

## 📚 API Documentation

### Core Endpoints

#### Health Check
```http
GET /health
```
**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-08-24T11:58:00"
}
```

#### Korean Maritime Regions
```http
GET /regions
```
**Response:**
```json
{
  "regions": {
    "west_sea": {"name": "서해", "bbox": [124.5, 35.5, 126.5, 37.5]},
    "south_sea": {"name": "남해", "bbox": [128.4, 34.6, 128.8, 35.0]},
    "east_sea": {"name": "동해", "bbox": [128.5, 37.0, 130.0, 38.5]}
  }
}
```

#### Marine Debris Analysis
```http
GET /region/{region_name}/analysis
```
**Parameters:**
- `region_name`: Korean region (west_sea, south_sea, east_sea)
- `days_back`: Analysis period (default: 7)
- `cloud_cover`: Maximum cloud coverage (default: 20)

**Response:**
```json
{
  "region": "west_sea",
  "analysis_date": "2024-08-24T11:58:00",
  "satellite_data": {...},
  "spectral_indices": {
    "fdi": 0.25,
    "ndwi": -0.15,
    "mci": 0.08
  },
  "debris_detection": {
    "total_areas": 15,
    "confidence_score": 0.82,
    "coordinates": [...]
  }
}
```

### Specialized APIs

#### Enhanced ML Processing
```bash
# Start enhanced API
python apis/enhanced_api.py  # Port 8003
```

#### High-Resolution Analysis
```bash
# KOMPSAT integration
python apis/kompsat_high_res_api.py  # Port 8003
```

#### Free Enhancement Techniques
```bash
# Cost-free resolution enhancement
python apis/simple_free_enhancement.py  # Port 8005
```

---

## 🌊 Korean Maritime Monitoring

### Target Regions

| Region | Korean Name | Coverage | Key Features |
|--------|-------------|----------|-------------|
| **West Sea** | 서해 | Incheon vicinity | High debris accumulation, shipping traffic |
| **South Sea** | 남해 | Geoje Island area | Coastal plastic, fishing industry impact |
| **East Sea** | 동해 | Pohang-Ulsan coast | Industrial discharge, thermal monitoring |

### Spectral Indices Explained

#### FDI (Floating Debris Index)
- **Purpose**: Detect floating plastic debris
- **Range**: -1 to 1 (higher values indicate debris)
- **Optimized for**: Korean coastal waters

#### NDWI (Normalized Difference Water Index)
- **Purpose**: Water body identification
- **Range**: -1 to 1 (positive values = water)
- **Usage**: Debris vs. water classification

#### MCI (Maximum Chlorophyll Index)
- **Purpose**: Algae and organic matter detection
- **Range**: Variable (higher = more chlorophyll)
- **Application**: Distinguish organic from plastic debris

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|--------|
| `SENTINEL_HUB_CLIENT_ID` | Sentinel Hub OAuth client ID | ✅ | - |
| `SENTINEL_HUB_CLIENT_SECRET` | Sentinel Hub OAuth secret | ✅ | - |
| `PORT` | API server port | ❌ | 8002 |
| `CORS_ORIGINS` | Allowed CORS origins | ❌ | Auto |

### Regional Customization

Edit region definitions in `real_sentinel_api.py`:
```python
KOREA_REGIONS = {
    "custom_region": {
        "name": "Custom Area",
        "bbox": [longitude_min, latitude_min, longitude_max, latitude_max]
    }
}
```

## 🚀 Deployment

### Render Cloud Platform (Recommended)

1. **Fork Repository** on GitHub
2. **Connect to Render**:
   - Service Type: Web Service
   - Repository: Your forked repo
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python real_sentinel_api.py`

3. **Set Environment Variables**:
   ```
   SENTINEL_HUB_CLIENT_ID=your_client_id
   SENTINEL_HUB_CLIENT_SECRET=your_client_secret
   ```

4. **Deploy**: Automatic deployment on git push

### Docker Deployment

```bash
# Build container
docker build -t satchat .

# Run with environment variables
docker run -p 8002:8002 \
  -e SENTINEL_HUB_CLIENT_ID=your_id \
  -e SENTINEL_HUB_CLIENT_SECRET=your_secret \
  satchat
```

### Local Production Setup

```bash
# Install production dependencies
pip install -r requirements.txt

# Set production environment
export NODE_ENV=production

# Start with gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker real_sentinel_api:app
```

---

## 🧪 Development

### Project Structure
```
sat_chat/
├── 📄 real_sentinel_api.py      # Main production API
├── 📄 multi_analysis.html       # Interactive dashboard  
├── 📄 serve_dashboard.py        # Local development server
├── 📁 apis/                     # Specialized API modules
│   ├── enhanced_api.py          # ML-enhanced processing
│   ├── kompsat_high_res_api.py  # High-resolution analysis
│   └── ...
├── 📁 web/                      # Frontend assets
├── 📁 src/                      # Core application source
├── 📁 frontend/                 # React components (optional)
└── 📋 docs/                     # Documentation
```

### Adding New Features

1. **API Endpoints**: Extend `real_sentinel_api.py`
2. **Analysis Methods**: Add to `/apis/` directory
3. **Frontend**: Update `multi_analysis.html`
4. **Documentation**: Update relevant docs

### Testing

```bash
# Run local tests
python -m pytest tests/

# Test API endpoints
curl http://localhost:8002/health
curl http://localhost:8002/regions
```

## 🔧 Troubleshooting

### Common Issues

#### Deployment Issues

**502 Bad Gateway on Render**
```bash
# Check if all dependencies are properly installed
pip install -r requirements.txt

# Verify environment variables are set
echo $SENTINEL_HUB_CLIENT_ID
echo $SENTINEL_HUB_CLIENT_SECRET

# Test API locally first
python real_sentinel_api.py
curl http://localhost:8002/health
```

**Build Failures**
- Ensure Python version compatibility (3.11+)
- Check for conflicting dependencies in requirements.txt
- Verify all import statements are correct

**Port Binding Issues**
```bash
# Check if port is already in use
netstat -tulpn | grep :8002

# Kill existing process if needed
pkill -f "python real_sentinel_api.py"
```

#### API Issues

**Authentication Failures**
```bash
# Verify Sentinel Hub credentials
curl -X POST "https://services.sentinel-hub.com/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=YOUR_ID&client_secret=YOUR_SECRET"
```

**Data Retrieval Errors**
- Check internet connectivity
- Verify Sentinel Hub service status
- Ensure coordinates are within valid ranges
- Confirm cloud coverage thresholds

**CORS Issues**
```javascript
// Ensure frontend origin is allowed
const response = await fetch('https://your-api.onrender.com/health', {
  method: 'GET',
  headers: {
    'Content-Type': 'application/json',
  }
});
```

#### Development Issues

**Module Import Errors**
```bash
# Install missing dependencies
pip install fastapi uvicorn sentinelhub requests

# Check Python path
python -c "import sys; print(sys.path)"
```

**Environment Variables Not Loading**
```bash
# Create .env file in project root
cp .env.example .env
nano .env

# Export variables manually
export SENTINEL_HUB_CLIENT_ID="your_id_here"
export SENTINEL_HUB_CLIENT_SECRET="your_secret_here"
```

### Performance Optimization

**Slow API Responses**
- Reduce analysis period (days_back parameter)
- Increase cloud coverage threshold to find images faster
- Use caching for repeated requests
- Optimize spectral index calculations

**Memory Issues**
```bash
# Monitor memory usage
htop

# Reduce image resolution in processing
# Implement pagination for large datasets
```

### Logging and Debugging

**Enable Debug Mode**
```python
# Add to real_sentinel_api.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Check Application Logs**
```bash
# Local development
python real_sentinel_api.py 2>&1 | tee app.log

# Render deployment
# View logs in Render dashboard
```

### Health Checks

**API Health Verification**
```bash
# Local testing
curl http://localhost:8002/health

# Production testing
curl https://your-app.onrender.com/health

# Expected response:
# {"status": "healthy", "timestamp": "2024-08-24T12:00:00Z"}
```

**Service Monitoring**
- Set up automated health checks
- Monitor response times
- Track error rates
- Implement alerting for failures

---

## 📝 라이센스

비공개 소프트웨어 - Telefix 소유

## 📧 문의

- Email: dev@telefix.co.kr
- Website: https://telefix.co.kr

---

© 2024 Telefix. All rights reserved.