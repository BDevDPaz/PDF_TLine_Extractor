import React, { useState } from 'react';
import axios from 'axios';

export default function Uploader({ onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError('');
    setMessage('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Por favor, selecciona un archivo PDF.');
      return;
    }
    
    setIsLoading(true);
    setError('');
    setMessage('');
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('/api/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setMessage(response.data.message);
      onUploadSuccess(); // Actualizar la lista de líneas en el dashboard
    } catch (err) {
      setError(err.response?.data?.error || 'Ocurrió un error al subir el archivo.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <form onSubmit={handleSubmit}>
        <label htmlFor="file-upload" className="block text-sm font-medium text-gray-700 mb-2">
          Subir Factura PDF
        </label>
        <div className="flex">
          <input 
            id="file-upload" 
            type="file" 
            onChange={handleFileChange} 
            accept=".pdf" 
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
          />
          <button 
            type="submit" 
            disabled={isLoading || !file}
            className="ml-4 inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400"
          >
            {isLoading ? 'Procesando...' : 'Procesar'}
          </button>
        </div>
        {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
        {message && <p className="text-green-500 text-sm mt-2">{message}</p>}
      </form>
    </div>
  );
}