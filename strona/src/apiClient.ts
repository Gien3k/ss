// src/apiClient.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
});

// Interceptor do dodawania tokenu do każdego żądania
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('accessToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// NOWY Interceptor do obsługi błędów autoryzacji
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Jeśli token jest nieważny, wyloguj użytkownika
      localStorage.removeItem('accessToken');
      // Odśwież stronę, aby przenieść do ekranu logowania
      window.location.reload();
    }
    return Promise.reject(error);
  }
);

export default apiClient;
