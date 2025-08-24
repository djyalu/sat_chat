// SatChat Service Worker - Offline-First Marine Debris Analysis
const CACHE_NAME = 'satchat-v2.0.0-client-ai';
const CACHE_URLS = [
    './',
    './index.html',
    './manifest.json',
    'https://cdn.tailwindcss.com',
    'https://cdn.jsdelivr.net/npm/chart.js',
    'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',
    'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
    'https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@latest/dist/tf.min.js',
    'https://cdn.jsdelivr.net/npm/@tensorflow/tfjs-layers@latest/dist/tf-layers.min.js'
];

// Install event - cache resources
self.addEventListener('install', event => {
    console.log('🚀 SatChat SW: Installing...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('📦 SatChat SW: Caching app resources');
                return cache.addAll(CACHE_URLS);
            })
            .then(() => {
                console.log('✅ SatChat SW: Installation complete');
                return self.skipWaiting();
            })
    );
});

// Activate event - clean old caches
self.addEventListener('activate', event => {
    console.log('⚡ SatChat SW: Activating...');
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('🗑️ SatChat SW: Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            console.log('✅ SatChat SW: Activation complete');
            return self.clients.claim();
        })
    );
});

// Fetch event - serve from cache first, then network
self.addEventListener('fetch', event => {
    // Skip API calls - let them go to network
    if (event.request.url.includes('/api/') || 
        event.request.url.includes('sat-chat.onrender.com')) {
        return;
    }
    
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                // Return cached version or fetch from network
                if (response) {
                    console.log('💾 SatChat SW: Serving from cache:', event.request.url);
                    return response;
                }
                
                console.log('🌐 SatChat SW: Fetching from network:', event.request.url);
                return fetch(event.request).then(response => {
                    // Cache successful responses
                    if (response.status === 200) {
                        const responseClone = response.clone();
                        caches.open(CACHE_NAME).then(cache => {
                            cache.put(event.request, responseClone);
                        });
                    }
                    return response;
                });
            })
            .catch(() => {
                // Offline fallback
                console.log('❌ SatChat SW: Offline - serving fallback');
                return new Response(
                    '<h1>🌊 SatChat Offline</h1><p>Client-side analysis available without internet</p>',
                    { headers: { 'Content-Type': 'text/html' } }
                );
            })
    );
});

// Message handling for cache updates
self.addEventListener('message', event => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        console.log('⚡ SatChat SW: Skipping waiting...');
        self.skipWaiting();
    }
    
    if (event.data && event.data.type === 'CACHE_ANALYSIS') {
        console.log('💾 SatChat SW: Caching analysis result');
        const { region, data } = event.data;
        caches.open(CACHE_NAME).then(cache => {
            const response = new Response(JSON.stringify(data));
            cache.put(`/analysis/${region}`, response);
        });
    }
});

console.log('🛰️ SatChat Service Worker v2.0.0 loaded - Offline-First Client AI');