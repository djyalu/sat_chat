#!/usr/bin/env python3
"""
SatChat Architecture Cleanup - 아키텍처 일관성 정리
Client-Heavy + Ultra-Minimal Proxy 아키텍처로 정렬
"""

import os
import shutil
from pathlib import Path

def cleanup_architecture():
    """아키텍처 일관성을 위한 정리 작업"""
    
    print("🧹 SatChat Architecture Cleanup Starting...")
    
    # 1. 사용하지 않는 API 파일들 아카이브
    legacy_apis = [
        "app.py",
        "main.py", 
        "simple_app.py",
        "simple_test_app.py",
        "enhanced_render_api.py",
        "enhanced_simple_api.py",
        "real_sentinel_api.py",
        "satchat_lite.py"
    ]
    
    archive_dir = Path("archive/legacy_apis")
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    for api_file in legacy_apis:
        if Path(api_file).exists():
            print(f"📦 Archiving {api_file}")
            shutil.move(api_file, archive_dir / api_file)
    
    # 2. 중복 requirements 파일들 정리
    legacy_reqs = [
        "requirements.txt",
        "requirements-enhanced.txt", 
        "requirements-lite.txt"
    ]
    
    req_archive_dir = Path("archive/requirements")
    req_archive_dir.mkdir(parents=True, exist_ok=True)
    
    for req_file in legacy_reqs:
        if Path(req_file).exists():
            print(f"📦 Archiving {req_file}")
            shutil.move(req_file, req_archive_dir / req_file)
    
    # 3. 중복 frontend 디렉토리들 정리
    legacy_frontends = ["dashboard", "web", "static"]
    
    frontend_archive_dir = Path("archive/frontends")
    frontend_archive_dir.mkdir(parents=True, exist_ok=True)
    
    for frontend_dir in legacy_frontends:
        if Path(frontend_dir).exists() and Path(frontend_dir).is_dir():
            print(f"📦 Archiving {frontend_dir}/")
            shutil.move(frontend_dir, frontend_archive_dir / frontend_dir)
    
    # 4. 핵심 파일들만 유지
    core_files = {
        "API": "minimal_proxy_api.py",
        "Requirements": "requirements-minimal.txt", 
        "Frontend": "docs/",
        "Deployment": "render.yaml"
    }
    
    print("\n✅ Core Architecture Files:")
    for category, file_path in core_files.items():
        status = "✅" if Path(file_path).exists() else "❌"
        print(f"  {status} {category}: {file_path}")
    
    # 5. 아키텍처 다이어그램 생성
    create_architecture_diagram()
    
    print("\n🎯 Architecture Cleanup Complete!")
    print("📋 Current Stack:")
    print("  • Frontend: GitHub Pages PWA + TensorFlow.js")
    print("  • Backend: Ultra-Minimal Proxy (20MB)")
    print("  • Processing: 100% Client-Side")
    print("  • Storage: Browser Cache + Service Worker")

def create_architecture_diagram():
    """현재 아키텍처 다이어그램 생성"""
    
    diagram = """
# SatChat Client-Heavy Architecture

```
┌─────────────────────────────────────┐    ┌─────────────────────────┐
│           GitHub Pages              │───▶│      Render Proxy       │
│  ┌─────────────────────────────┐    │    │  ┌───────────────────┐  │
│  │     PWA Frontend            │    │    │  │ minimal_proxy_api │  │
│  │  • TensorFlow.js AI         │    │    │  │     (20MB)        │  │
│  │  • Multi-Index Analysis     │    │    │  │  • Metadata only  │  │
│  │  • Offline-First            │    │    │  │  • Auth proxy     │  │
│  │  • Service Worker Cache     │    │    │  │  • Region info    │  │
│  └─────────────────────────────┘    │    │  └───────────────────┘  │
│                                     │    └─────────────────────────┘
│  ┌─────────────────────────────┐    │
│  │     Client Processing       │    │              
│  │  • 5-Index Spectral        │    │    External APIs (Optional)
│  │  • CNN Debris Detection    │    │    ┌─────────────────────────┐
│  │  • Real-time Analysis      │    │───▶│   Sentinel Hub          │
│  │  • Hotspot Generation      │    │    │   Weather APIs          │
│  └─────────────────────────────┘    │    └─────────────────────────┘
└─────────────────────────────────────┘

Performance:
• Frontend: 100% availability, <500ms processing
• Backend: 20MB RAM, sleep-resistant
• Total: Zero server processing load
```
"""
    
    Path("ARCHITECTURE.md").write_text(diagram)
    print("📄 Created ARCHITECTURE.md")

if __name__ == "__main__":
    cleanup_architecture()