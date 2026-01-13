import axios from 'axios';

// Configurar Axios con la base URL del backend
const apiClient = axios.create({
  baseURL: 'http://localhost:8000', // URL del backend
  headers: {
    'Content-Type': 'application/json',
  },
});

export default apiClient;