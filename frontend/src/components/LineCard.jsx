import React from 'react';
import { Link } from 'react-router-dom';

export default function LineCard({ line }) {
    return (
        <Link to={`/line/${line.id}`} className="block p-4 bg-white rounded-lg shadow hover:shadow-lg transition-shadow">
            <h3 className="font-semibold text-lg text-gray-800">{line.phone_number}</h3>
            <p className="text-sm text-blue-600 mt-2">Ver detalles &rarr;</p>
        </Link>
    );
}