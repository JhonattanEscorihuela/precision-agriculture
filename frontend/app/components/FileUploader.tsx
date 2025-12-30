'use client'; // Necesario para usar hooks como useState en Next.js App Router

import React from 'react';

type Props = {
    onUpload: (file: File) => void;
};

export default function FileUploader({ onUpload }: Props) {
    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) onUpload(file);
    };

    return (
        <div className="my-4">
            <label className="block text-sm font-medium text-gray-700">Subir Imagen Satelital</label>
            <input
                type="file"
                accept="image/*"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring focus:ring-indigo-200"
                onChange={handleFileChange}
            />
        </div>
    );
}