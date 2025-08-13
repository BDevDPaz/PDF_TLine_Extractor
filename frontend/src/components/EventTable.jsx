import React from 'react';

export default function EventTable({ columns, data }) {
    if (!data || data.length === 0) {
        return <p className="text-gray-500">No hay eventos para mostrar.</p>;
    }

    return (
        <div className="overflow-x-auto bg-white rounded-lg shadow">
            <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                    <tr>
                        {columns.map(col => (
                            <th key={col.accessor} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                {col.header}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                    {data.map(row => (
                        <tr key={row.id}>
                            {columns.map(col => (
                                <td key={`${row.id}-${col.accessor}`} className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                                    {col.accessor === 'timestamp' ? new Date(row[col.accessor]).toLocaleString() : row[col.accessor]}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}