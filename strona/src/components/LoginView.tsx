// src/components/LoginView.tsx
import React, { useState } from 'react';
import apiClient from '../apiClient';
import { AxiosError } from 'axios';

interface LoginViewProps {
  onLoginSuccess: (token: string) => void;
}

const LoginView: React.FC<LoginViewProps> = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState('testuser');
  const [password, setPassword] = useState('testpassword');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);

    try {
      const response = await apiClient.post('/token', params, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });
      onLoginSuccess(response.data.access_token);
    } catch (err) {
      const axiosError = err as AxiosError;
      if (axiosError.response) {
        setError('Nieprawidłowa nazwa użytkownika lub hasło.');
      } else {
        setError('Błąd połączenia z serwerem. Spróbuj ponownie później.');
      }
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50">
      <div className="w-full max-w-md p-8 space-y-8 bg-white rounded-lg shadow-md">
        <div>
          <h1 className="text-2xl font-bold text-center text-blue-700">SkillSense</h1>
          <h2 className="mt-2 text-xl font-bold text-center text-gray-900">Zaloguj się do swojego konta</h2>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="username-input" className="sr-only">
                Nazwa użytkownika
              </label>
              <input
                id="username-input"
                name="username"
                type="text"
                autoComplete="username"
                required
                className="relative block w-full px-3 py-2 text-gray-900 placeholder-gray-500 border border-gray-300 rounded-none appearance-none rounded-t-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="Nazwa użytkownika"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="password-input" className="sr-only">
                Hasło
              </label>
              <input
                id="password-input"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                className="relative block w-full px-3 py-2 text-gray-900 placeholder-gray-500 border border-gray-300 rounded-none appearance-none rounded-b-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="Hasło"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          {error && <p className="text-sm text-center text-red-600">{error}</p>}

          <div>
            <button
              type="submit"
              disabled={isLoading}
              className="relative flex justify-center w-full px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md group hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {isLoading ? 'Logowanie...' : 'Zaloguj się'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default LoginView;
