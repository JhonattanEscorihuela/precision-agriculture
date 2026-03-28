'use client';

import { useState } from 'react';

export default function FileUploader({
    onUpload,
    accept = 'image/*,.geojson,.kml,.json',
    maxSize = 10
}: {
    onUpload: (file: File) => void;
    accept?: string;
    maxSize?: number;
}) {
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [error, setError] = useState('');

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            if (file.size > maxSize * 1024 * 1024) {
                setError(`El archivo excede ${maxSize}MB`);
                return;
            }
            setSelectedFile(file);
            onUpload(file);
        }
    };

    return (
        <div className="w-full">
            <label className="flex items-center gap-2 text-sm font-semibold text-slate-800 mb-3">
                <span className="text-xl">📁</span>
                Subir Archivo
            </label>

            <div className={`border-2 border-dashed rounded-xl p-8 text-center transition-all
                ${selectedFile
                    ? 'border-vegetation-healthy bg-vegetation-healthy/5'
                    : 'border-satellite-blue/30 bg-satellite-blue/5 hover:border-satellite-blue/50'
                }
                ${error ? 'border-vegetation-critical bg-vegetation-critical/5' : ''}`}
            >
                <input
                    type="file"
                    id="file-input"
                    className="hidden"
                    accept={accept}
                    onChange={handleChange}
                />
                <label htmlFor="file-input" className="cursor-pointer flex flex-col items-center gap-2">
                    {selectedFile ? (
                        <>
                            <span className="text-4xl">📄</span>
                            <span className="font-semibold text-slate-800">{selectedFile.name}</span>
                            <span className="font-mono text-sm text-slate-600">
                                {(selectedFile.size / 1024).toFixed(2)} KB
                            </span>
                        </>
                    ) : (
                        <>
                            <span className="text-4xl">☁️</span>
                            <span className="font-semibold text-slate-800">Arrastra un archivo o haz clic</span>
                            <span className="text-sm text-slate-600">Máximo {maxSize}MB</span>
                        </>
                    )}
                </label>
            </div>

            {error && (
                <div className="mt-3 px-4 py-3 bg-vegetation-critical/10 border border-vegetation-critical/30 rounded-lg flex items-center gap-2 text-sm text-vegetation-critical">
                    <span className="text-lg">⚠️</span>
                    <span>{error}</span>
                </div>
            )}
        </div>
    );
}
