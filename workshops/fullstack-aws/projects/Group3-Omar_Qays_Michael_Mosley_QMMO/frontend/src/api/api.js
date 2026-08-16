import axios from 'axios';

// Creates one Axios client that all frontend API calls can use
const api = axios.create({
  baseURL: 'http://127.0.0.1:8000',
});

export default api;