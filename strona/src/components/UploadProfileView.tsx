// src/components/UploadProfileView.tsx
import React, { useState } from 'react';
import { Loader2, Send, UploadCloud } from 'lucide-react';
import apiClient from '../apiClient.ts';
import { AxiosError } from 'axios';

const UploadProfileView = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [message, setMessage] = useState('');

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setSelectedFile(event.target.files[0]);
      setMessage(`Wybrano plik: ${event.target.files[0].name}`);
    }
  };

  const handleSubmit = async () => {
    if (!selectedFile) {
      setMessage('Proszę najpierw wybrać plik.');
      return;
    }
    setIsUploading(true);
    setMessage('Wysyłanie i przetwarzanie pliku...');

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      // POPRAWKA: Usunięto ukośnik z '/upload-cv/'
      const response = await apiClient.post('/upload-cv', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setMessage(`Sukces! Utworzono profil dla: ${response.data.name} ${response.data.surname}.`);
      setSelectedFile(null);
    } catch (err) {
        const error = err as AxiosError<{ detail: string }>;
        console.error("Błąd podczas przesyłania CV:", error);
        if (error.response) {
            setMessage(`Błąd: ${error.response.data.detail || 'Wystąpił błąd serwera.'}`);
        } else {
            setMessage('Błąd: Nie udało się połączyć z serwerem.');
        }
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="p-6 bg-white h-full">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">Dodaj Profil Kandydata</h1>
      {/* ... reszta JSX bez zmian ... */}
      <div className="bg-white border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
          <UploadCloud className="mx-auto h-12 w-12 text-gray-400" />
          <p className="mt-4 text-sm text-gray-600">
            <label htmlFor="file-upload" className="font-medium text-blue-600 hover:text-blue-500 cursor-pointer">
              Wybierz plik
            </label>
            lub przeciągnij go tutaj (.pdf).
          </p>
          <input id="file-upload" type="file" className="sr-only" onChange={handleFileChange} accept=".pdf"/>
        </div>
        
      {message && <p className="mt-4 text-center text-sm text-gray-600">{message}</p>}

      <div className="mt-6">
        <button
          onClick={handleSubmit}
          disabled={isUploading || !selectedFile}
          className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-2"
        >
          {isUploading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
          <span>{isUploading ? 'Przetwarzanie...' : 'Wyślij i Przeanalizuj'}</span>
        </button>
      </div>
    </div>
  );
};

export default UploadProfileView;
