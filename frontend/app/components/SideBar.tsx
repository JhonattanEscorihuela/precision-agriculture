'use client'; // Convertimos el Sidebar en un Client Component

import React from 'react';
import Link from 'next/link'; // Importamos para navegación
import { usePolygons } from '../context/PolygonContext';

type SidebarItem = {
    title: string;
    path: string; // Nueva propiedad para navegación
    icon?: string; // Placeholder para futuros íconos
};

const items: SidebarItem[] = [
    { title: 'Agricultura de Precisión', path: '/' },
    { title: 'Mis Cultivos', path: '/cultivos' },
    { title: 'Cargar Nueva Parcela', path: '/nueva-parcela' },
];

export default function Sidebar() {
    const { polygons } = usePolygons(); // Usamos el contexto para obtener los polígonos

    return (
        <div className="h-screen w-[12vw] bg-gray-800 grid grid-cols-1 grid-rows-5">
            {/* Logo Principal */}
            <div className="text-center row-start-1">
                <img src="/logo-universidad.png" alt="Universidad de Carabobo" className="h-[10vh] w-auto mx-auto mb-4" />
                <h1 className="text-white text-lg font-semibold leading-tight">
                    Centro de Procesamiento de Imágenes
                </h1>
            </div>

            {/* Menú de opciones dinámicas */}
            <nav className="w-full row-start-2">
                {items.map((item, index) => (
                    <Link href={item.path} key={index}>
                        <button
                            className="w-[90%] mx-auto flex items-center justify-center text-white bg-gray-700 hover:bg-gray-600 py-3 rounded mb-4 text-base"
                        >
                            {item.title}
                        </button>
                    </Link>
                ))}
            </nav>



            {/* Perfil del Usuario */}
            <div className="flex flex-col items-center justify-center mt-36 row-start-5">
                <img
                    src="/user-avatar.png"
                    alt="Mi perfil"
                    className="h-[4vh] w-[4vh] rounded-full border-2 border-white"
                />
                <h2 className="text-white text-sm mt-2">Mi Perfil</h2>
            </div>
        </div>
    );
}