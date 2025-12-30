'use client';

import React, { useState } from 'react';
import FileUploader from './components/FileUploader';
import Map from './components/Map';
import ResultsTable from './components/ResultsTable';

export default function Home() {
  const [results, setResults] = useState<Array<{ key: string; value: string }>>([]);

  const handleUpload = (file: File) => {
    // Simula resultados al cargar una imagen.
    console.log('Archivo subido:', file.name);
    setResults([
      { key: 'Salud del Cultivo', value: 'Buena' },
      { key: 'Rendimiento Estimado', value: '3000 kg/ha' },
      { key: 'Fase Fonológica', value: 'Vegetativa' },
    ]);
  };

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-6">Agricultura de Precisión</h1>
      <FileUploader onUpload={handleUpload} />
      <Map />
      {results.length > 0 && <ResultsTable results={results} />}
    </div>
  );
}