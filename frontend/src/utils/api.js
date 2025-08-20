import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
});

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
