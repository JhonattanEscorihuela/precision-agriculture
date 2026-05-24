'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { usePolygons } from '../context/PolygonContext';
import { useAuth } from '../context/AuthContext';

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
    const { user, logout } = useAuth();
    const pathname = usePathname();
    const [isOpen, setIsOpen] = useState(false);

    const closeSidebar = () => setIsOpen(false);

    return (
        <>
            {/* Hamburger button - solo visible en mobile */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="lg:hidden fixed top-4 left-4 z-[2000] w-12 h-12 bg-satellite-deep rounded-xl shadow-lg flex items-center justify-center text-white hover:bg-satellite-darker transition-colors"
                aria-label="Toggle menu"
            >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    {isOpen ? (
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    ) : (
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                    )}
                </svg>
            </button>

            {/* Overlay - solo en mobile cuando está abierto */}
            {isOpen && (
                <div
                    className="lg:hidden fixed inset-0 bg-black/50 z-[1998]"
                    onClick={closeSidebar}
                />
            )}

            {/* Sidebar */}
            <div className={`
                fixed lg:relative
                h-screen w-[280px]
                bg-gradient-to-br from-satellite-deep to-satellite-darker
                flex flex-col overflow-hidden shadow-2xl
                z-[1999]
                transition-transform duration-300 ease-in-out
                ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
            `}>
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
                        <Link href={item.path} key={index} onClick={closeSidebar}>
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
            <div className="p-6 border-t border-satellite-blue/20 relative z-[2] space-y-3">
                <div className="flex items-center gap-4 p-3 bg-white/5 backdrop-blur-md border border-satellite-blue/20 rounded-xl">
                    <div className="relative w-10 h-10">
                        <div className="w-full h-full rounded-full bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center border-2 border-satellite-blue/50 shadow-[0_0_12px_rgba(16,185,129,0.4)]">
                            <span className="text-white font-bold text-sm">{user?.full_name?.charAt(0).toUpperCase() || 'U'}</span>
                        </div>
                        <div className="absolute bottom-0 right-0 w-3 h-3 bg-vegetation-healthy border-2 border-satellite-deep rounded-full shadow-[0_0_8px_rgba(16,185,129,1)] animate-pulse-glow" />
                    </div>
                    <div className="flex-1 min-w-0">
                        <h2 className="text-white text-sm font-semibold truncate">{user?.full_name}</h2>
                        <p className="text-white/60 text-xs truncate">{user?.email}</p>
                    </div>
                </div>

                {/* Botón Logout */}
                <button
                    onClick={logout}
                    className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-red-500/10 backdrop-blur-md border border-red-400/30 rounded-xl text-red-300 text-sm font-medium transition-all duration-300 hover:bg-red-500/20 hover:border-red-400/50 hover:shadow-lg"
                >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                    </svg>
                    Cerrar sesión
                </button>
            </div>
        </div>
        </>
    );
}