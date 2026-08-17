import axios from 'axios';

// Creates one Axios client that all frontend API calls can use
const api = axios.create({
  baseURL: 'https://d1a13cxnr8.execute-api.us-east-1.amazonaws.com',
});

export default api;