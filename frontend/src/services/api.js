import axios from 'axios';
import { toast } from 'react-toastify';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

// Axios 인스턴스 생성
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth-token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 응답 인터셉터
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth-token');
      window.location.href = '/login';
      toast.error('세션이 만료되었습니다. 다시 로그인해주세요.');
    } else if (error.response?.status === 500) {
      toast.error('서버 오류가 발생했습니다.');
    }
    return Promise.reject(error);
  }
);

// API 엔드포인트
export const authAPI = {
  login: (credentials) => api.post('/auth/login', credentials),
  logout: () => api.post('/auth/logout'),
  getProfile: () => api.get('/auth/profile'),
};

export const satelliteAPI = {
  getImages: (params) => api.get('/images', { params }),
  getImageById: (id) => api.get(`/images/${id}`),
  processImage: (id) => api.post(`/images/${id}/process`),
};

export const detectionAPI = {
  getDetections: (params) => api.get('/detections', { params }),
  getDetectionById: (id) => api.get(`/detections/${id}`),
  updateDetection: (id, data) => api.put(`/detections/${id}`, data),
};

export const alertAPI = {
  getAlerts: (params) => api.get('/alerts', { params }),
  createAlert: (data) => api.post('/alerts', data),
  updateAlert: (id, data) => api.put(`/alerts/${id}`, data),
  deleteAlert: (id) => api.delete(`/alerts/${id}`),
};

export const monitoringAPI = {
  getAreas: () => api.get('/monitoring/areas'),
  createArea: (data) => api.post('/monitoring/areas', data),
  updateArea: (id, data) => api.put(`/monitoring/areas/${id}`, data),
  deleteArea: (id) => api.delete(`/monitoring/areas/${id}`),
};

export const sentinelHubAPI = {
  getStatistics: (params) => api.get('/sentinel-hub/statistics/marine-debris', { params }),
  searchScenes: (params) => api.post('/sentinel-hub/search', params),
  processScene: (sceneId) => api.post(`/sentinel-hub/process/${sceneId}`),
};

export const byocAPI = {
  getCollectionInfo: () => api.get('/byoc/collection/info'),
  listCollections: () => api.get('/byoc/collections'),
  queryData: (params) => api.get('/byoc/query', { params }),
  ingestData: (data) => api.post('/byoc/ingest', data),
  uploadCOG: (file, params) => {
    const formData = new FormData();
    formData.append('file', file);
    Object.keys(params).forEach(key => {
      formData.append(key, params[key]);
    });
    return api.post('/byoc/upload-cog', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  getStatistics: (params) => api.get('/byoc/statistics', { params }),
};