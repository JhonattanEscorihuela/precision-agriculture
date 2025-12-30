'use client';

import React from 'react';

type Props = {
    results: Array<{ key: string; value: string }>;
};

export default function ResultsTable({ results }: Props) {
    return (
        <div className="my-8">
            <table className="min-w-full divide-y divide-gray-200 bg-white rounded-lg">
                <thead>
                    <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Variable</th>
                        <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Valor</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                    {results.map((result, index) => (
                        <tr key={index}>
                            <td className="px-6 py-4 text-sm text-gray-800">{result.key}</td>
                            <td className="px-6 py-4 text-sm text-gray-800">{result.value}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}