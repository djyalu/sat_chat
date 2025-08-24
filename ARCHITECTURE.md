
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
