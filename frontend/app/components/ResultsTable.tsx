'use client';

type ResultRow = {
    key: string;
    value: string | number;
    icon?: string;
    status?: 'healthy' | 'alert' | 'critical';
};

export default function ResultsTable({ title, results, variant = 'default' }: {
    title?: string;
    results: ResultRow[];
    variant?: 'default' | 'compact';
}) {
    const statusColors = {
        healthy: 'bg-vegetation-healthy',
        alert: 'bg-vegetation-alert',
        critical: 'bg-vegetation-critical'
    };

    return (
        <div className="w-full bg-white rounded-2xl shadow-md overflow-hidden border-2 border-satellite-blue/10">
            {title && (
                <div className="px-6 py-4 bg-gradient-to-r from-satellite-blue/5 to-satellite-deep/5 border-b-2 border-satellite-blue/10">
                    <h3 className="text-xl font-bold text-slate-800 flex items-center gap-3">
                        <span className="text-2xl">📊</span>
                        {title}
                    </h3>
                </div>
            )}

            <div className="overflow-x-auto">
                <table className="w-full">
                    <thead className="bg-satellite-blue/5">
                        <tr>
                            <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider text-satellite-deep border-b-2 border-satellite-blue/10">Variable</th>
                            <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider text-satellite-deep border-b-2 border-satellite-blue/10">Valor</th>
                            <th className="px-6 py-4 text-center text-xs font-bold uppercase tracking-wider text-satellite-deep border-b-2 border-satellite-blue/10">Estado</th>
                        </tr>
                    </thead>
                    <tbody>
                        {results.map((result, index) => (
                            <tr key={index} className="border-b border-satellite-blue/5 hover:bg-satellite-blue/5 transition-colors">
                                <td className="px-6 py-4 flex items-center gap-3 font-semibold text-slate-800">
                                    {result.icon && <span className="text-xl">{result.icon}</span>}
                                    <span>{result.key}</span>
                                </td>
                                <td className="px-6 py-4 font-mono font-semibold text-satellite-deep">
                                    {result.value}
                                </td>
                                <td className="px-6 py-4 text-center">
                                    {result.status && (
                                        <div className={`w-3 h-3 mx-auto rounded-full ${statusColors[result.status]} shadow-lg animate-pulse`} />
                                    )}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {results.length === 0 && (
                <div className="text-center py-16 px-8">
                    <span className="text-6xl mb-4 block opacity-50">📭</span>
                    <p className="text-slate-600">No hay resultados disponibles</p>
                </div>
            )}
        </div>
    );
}
