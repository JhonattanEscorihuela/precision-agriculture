'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { usePolygons } from '../context/PolygonContext';

type SidebarItem = {
    title: string;
    path: string;
    icon: string;
};

const items: SidebarItem[] = [
    { title: 'Mapa Principal', path: '/', icon: '🛰️' },
    { title: 'Mis Cultivos', path: '/cultivos', icon: '🌾' },
    { title: 'Nueva Parcela', path: '/nueva-parcela', icon: '➕' },
];

export default function Sidebar() {
    const { polygons } = usePolygons();
    const pathname = usePathname();

    return (
        <div className="h-screen w-[280px] bg-gradient-to-br from-satellite-deep to-satellite-darker relative flex flex-col overflow-hidden shadow-2xl">
            {/* Scan lines effect */}
            <div className="absolute inset-0 pointer-events-none z-[1] scan-lines-effect" />

            {/* Logo Principal */}
            <div className="p-8 pt-8 text-center relative z-[2] border-b border-satellite-blue/20">
                <div className="relative inline-block mb-4">
                    <img
                        src="/logo-universidad.png"
                        alt="Universidad de Carabobo"
                        className="h-20 w-auto brightness-110 drop-shadow-[0_0_10px_rgba(14,165,233,0.3)] animate-pulse-glow"
                    />
                </div>
                <h1 className="text-white text-sm font-semibold leading-tight tracking-wide drop-shadow-lg mb-4">
                    Centro de<br />Procesamiento<br />de Imágenes
                </h1>
                {polygons.length > 0 && (
                    <div className="inline-flex items-center gap-2 bg-vegetation-healthy/15 backdrop-blur-xl border border-vegetation-healthy/30 rounded-full px-4 py-2 mt-3">
                        <span className="font-mono text-vegetation-vibrant text-lg font-bold">{polygons.length}</span>
                        <span className="text-white/80 text-xs font-medium">Parcelas</span>
                    </div>
                )}
            </div>

            {/* Menú de navegación */}
            <nav className="flex-1 p-6 flex flex-col gap-3 relative z-[2]">
                {items.map((item, index) => {
                    const isActive = pathname === item.path;
                    return (
                        <Link href={item.path} key={index}>
                            <button
                                className={`w-full flex items-center gap-4 px-5 py-4 bg-white/5 backdrop-blur-md border rounded-xl text-white text-sm font-medium text-left cursor-pointer transition-all duration-400 ease-out relative overflow-hidden group
                                    ${isActive
                                        ? 'bg-satellite-blue/20 border-satellite-blue/80 shadow-[0_0_24px_rgba(14,165,233,0.4)] translate-x-2'
                                        : 'border-satellite-blue/20 hover:bg-satellite-blue/15 hover:border-satellite-blue/60 hover:shadow-[0_0_20px_rgba(14,165,233,0.3)] hover:translate-x-2'
                                    }`}
                            >
                                <span className="text-2xl drop-shadow-md">{item.icon}</span>
                                <span className="flex-1">{item.title}</span>
                                {isActive && (
                                    <div className="absolute right-0 top-0 bottom-0 w-1  rounded-l" />
                                )}
                                {/* Hover sweep effect */}
                                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-satellite-blue/10 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-600 ease-in-out" />
                            </button>
                        </Link>
                    );
                })}
            </nav>

            {/* Perfil del Usuario */}
            <div className="p-6 border-t border-satellite-blue/20 relative z-[2]">
                <div className="flex items-center gap-4 p-3 bg-white/5 backdrop-blur-md border border-satellite-blue/20 rounded-xl transition-all duration-300 cursor-pointer hover:bg-white/8 hover:border-satellite-blue/40 hover:shadow-lg">
                    <div className="relative w-12 h-12">
                        <div className="w-full h-full rounded-full bg-gradient-to-br from-data-accent to-data-purple flex items-center justify-center border-2 border-satellite-blue/50 shadow-[0_0_12px_rgba(139,92,246,0.4)]">
                            <span className="text-white font-bold text-base">UC</span>
                        </div>
                        <div className="absolute bottom-0.5 right-0.5 w-3 h-3 bg-vegetation-healthy border-2 border-satellite-deep rounded-full shadow-[0_0_8px_rgba(16,185,129,1)] animate-pulse-glow" />
                    </div>
                    <div className="flex-1">
                        <h2 className="text-white text-sm font-semibold">Mi Perfil</h2>
                        <p className="text-white/60 text-xs">Investigador</p>
                    </div>
                </div>
            </div>
        </div>
    );
}