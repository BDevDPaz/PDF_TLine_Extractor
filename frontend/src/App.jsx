import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import LineDetail from './pages/LineDetail';

function App() {
  return (
    <Router>
      <div className="bg-gray-100 min-h-screen font-sans">
        <header className="bg-white shadow-sm">
          <div className="container mx-auto px-4 py-4">
            <h1 className="text-2xl font-bold text-gray-800">
              Asistente de Análisis de Facturas
            </h1>
          </div>
        </header>
        <main className="container mx-auto p-4">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/line/:lineId" element={<LineDetail />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;