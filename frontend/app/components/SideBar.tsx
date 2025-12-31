import React from 'react';

type SidebarItem = {
    title: string;
    icon?: string; // Si en el futuro necesitas íconos
};

const items: SidebarItem[] = [
    { title: 'Agricultura de Precisión' },
    { title: 'Mis Cultivos' },
    { title: 'Cargar Nueva Parcela' },
];

export default function Sidebar() {
    return (
        <div className="h-screen w-[10vw] bg-gray-800 grid grid-cols-1 grid-rows-5 py-">
            {/* Logo Principal */}
            <div className="text-center row-start-1">
                <img src="./logo-universidad.png" alt="Universidad de Carabobo" className="h-[10vh] w-auto mx-auto mb-4" />
                <h1 className="text-white text-lg font-semibold leading-tight">
                    Centro de Procesamiento de Imágenes
                </h1>
            </div>

            {/* Menú de opciones dinámicas */}
            <nav className="w-full row-start-2">
                {items.map((item, index) => (
                    <button
                        key={index}
                        className="w-[90%] mx-auto flex items-center justify-center text-white bg-gray-700 hover:bg-gray-600 py-3 rounded mb-4 text-base"
                    >
                        {item.title}
                    </button>
                ))}
            </nav>

            {/* Perfil del Usuario */}
            <div className="flex flex-col items-center justify-center mt-36 row-start-5">
                <img
                    src="./user-avatar.png"
                    alt="User Profile"
                    className="h-[4vh] w-[4vh] rounded-full border-2 border-white"
                />
                <h2 className="text-white text-sm mt-2">Mi Perfil</h2>
            </div>
        </div>
    );
}