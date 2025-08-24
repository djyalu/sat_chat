# SatChat Project Structure

## 🚀 Main Application Files
- `real_sentinel_api.py` - Main production API server (Render deployment)
- `multi_analysis.html` - Integrated analysis dashboard  
- `serve_dashboard.py` - Local dashboard server (port 5555)
- `simple_app.py` - Simple test API for deployment testing

## 📁 Directory Structure

### `/apis` - API Modules
- `enhanced_api.py` - Enhanced features API with ML segmentation
- `kompsat_high_res_api.py` - High-resolution KOMPSAT satellite API
- `free_high_res_api.py` - Free resolution enhancement techniques
- `simple_free_enhancement.py` - Simple enhancement methods
- `sentinel_api.py` - Basic Sentinel-2 API

### `/web` - Web Frontend
- `index.html` - Main project landing page
- `real_data.html` - Real satellite data visualization

### `/src` - Core Application Source
- Complete SatChat application architecture
- Processing pipelines, ML models, services

### `/frontend` - React Frontend (Optional)
- Modern React-based user interface
- Component-based architecture

## 🔧 Configuration Files
- `requirements.txt` - Python dependencies for production
- `render.yaml` - Render deployment configuration  
- `.env.example` - Environment variables template

## 🛰️ Quick Start
```bash
# Local development
python real_sentinel_api.py

# Dashboard server
python serve_dashboard.py

# Enhanced features
python apis/enhanced_api.py
```

## 🌐 Deployment
- **Production**: Configured for Render (https://sat-chat.onrender.com)
- **Main API**: `real_sentinel_api.py` on dynamic port
- **Frontend**: `multi_analysis.html` served statically