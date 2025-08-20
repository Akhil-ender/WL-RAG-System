import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export const authAPI = {
  signup: (userData) => api.post('/signup', userData),
  login: (userData) => api.post('/login', userData),
  getMe: () => api.get('/me'),
};

export const chatAPI = {
  uploadPDF: (files) => {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    return api.post('/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  sendMessage: (question) => api.post('/chat', { question }),
  getStatus: () => api.get('/status'),
};

export const text2sqlAPI = {
  query: (question, top_k = 3) => api.post('/text2sql', { question, top_k }),
};

export const csvAPI = {
  upload: (file, table_name) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('table_name', table_name);
    return api.post('/upload-csv', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
};
