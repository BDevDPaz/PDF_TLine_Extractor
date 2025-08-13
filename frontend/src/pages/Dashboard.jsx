import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Uploader from '../components/Uploader';
import LineCard from '../components/LineCard';

export default function Dashboard() {
    const [lines, setLines] = useState([]);
    const [isLoading, setIsLoading] = useState(true);

    const fetchLines = async () => {
        setIsLoading(true);
        try {
            const response = await axios.get('/api/lines');
            setLines(response.data);
        } catch (error) {
            console.error("Error al obtener las líneas:", error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchLines();
    }, []);

    return (
        <div>
            <Uploader onUploadSuccess={fetchLines} />
            <div className="mt-8">
                <h2 className="text-xl font-semibold text-gray-700 mb-4">Líneas Telefónicas Procesadas</h2>
                {isLoading ? (
                    <p>Cargando líneas...</p>
                ) : lines.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {lines.map(line => (
                            <LineCard key={line.id} line={line} />
                        ))}
                    </div>
                ) : (
                    <p className="text-gray-500">No se han procesado facturas todavía. Sube un archivo para comenzar.</p>
                )}
            </div>
        </div>
    );
}