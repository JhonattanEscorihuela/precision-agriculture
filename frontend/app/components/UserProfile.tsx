'use client';

import { useState } from 'react';

export default function UserProfile({
    name = 'Usuario',
    role = 'Investigador',
    stats
}: {
    name?: string;
    role?: string;
    stats?: {
        totalParcels: number;
        totalArea: number;
        healthyParcels: number;
        alertParcels: number;
    };
}) {
    const [expanded, setExpanded] = useState(false);

    return (
        <div className="bg-white rounded-2xl shadow-md overflow-hidden border-2 border-satellite-blue/10 transition-all hover:shadow-xl hover:border-satellite-blue/30">
            <div className="flex items-center gap-4 p-5 cursor-pointer" onClick={() => setExpanded(!expanded)}>
                <div className="relative w-14 h-14">
                    <div className="w-full h-full rounded-full bg-gradient-to-br from-data-accent to-data-purple flex items-center justify-center border-[3px] border-white shadow-lg">
                        <span className="text-white font-bold text-xl">{name.substring(0, 2).toUpperCase()}</span>
                    </div>
                    <div className="absolute bottom-0.5 right-0.5 w-3.5 h-3.5 bg-vegetation-healthy border-[3px] border-white rounded-full animate-pulse" />
                </div>
                <div className="flex-1">
                    <h3 className="text-base font-bold text-slate-800">{name}</h3>
                    <p className="text-sm text-slate-600">{role}</p>
                </div>
                <button className={`text-satellite-blue transition-transform ${expanded ? 'rotate-180' : 'rotate-0'}`}>▼</button>
            </div>

            {expanded && stats && (
                <div className="px-5 pb-5 flex flex-col gap-3 border-t border-satellite-blue/10">
                    {[
                        { icon: '🌾', label: 'Parcelas Totales', value: stats.totalParcels },
                        { icon: '📐', label: 'Área Total', value: `${stats.totalArea.toFixed(2)} m²` },
                        { icon: '✅', label: 'Saludables', value: stats.healthyParcels, color: 'text-vegetation-healthy' },
                        { icon: '⚠️', label: 'En Alerta', value: stats.alertParcels, color: 'text-vegetation-alert' }
                    ].map((stat, i) => (
                        <div key={i} className="flex items-center gap-3 p-3 bg-satellite-blue/5 rounded-xl">
                            <span className="text-2xl">{stat.icon}</span>
                            <div className="flex-1 flex justify-between items-center">
                                <span className="text-sm text-slate-700">{stat.label}</span>
                                <span className={`font-mono font-bold ${stat.color || 'text-satellite-deep'}`}>{stat.value}</span>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
