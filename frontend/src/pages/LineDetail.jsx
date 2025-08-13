import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import Chat from '../components/Chat';
import EventTable from '../components/EventTable';

const TABS = ['Asistente IA', 'Llamadas', 'Textos', 'Datos'];

export default function LineDetail() {
    const { lineId } = useParams();
    const [details, setDetails] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [activeTab, setActiveTab] = useState(TABS[0]);
    
    useEffect(() => {
        const fetchDetails = async () => {
            setIsLoading(true);
            try {
                const response = await axios.get(`/api/lines/${lineId}/details`);
                setDetails(response.data);
            } catch (error) {
                console.error("Error al obtener los detalles:", error);
            } finally {
                setIsLoading(false);
            }
        };
        fetchDetails();
    }, [lineId]);

    const callColumns = [
        { header: 'Fecha y Hora', accessor: 'timestamp' },
        { header: 'Número', accessor: 'counterpart_number' },
        { header: 'Descripción', accessor: 'description' },
        { header: 'Duración (min)', accessor: 'duration_minutes' },
        { header: 'Categoría', accessor: 'ai_category' },
    ];

    if (isLoading) return <p>Cargando detalles de la línea...</p>;
    if (!details) return <p>No se encontraron datos para esta línea.</p>;

    return (
        <div>
            <Link to="/" className="text-blue-600 hover:underline mb-4 inline-block">&larr; Volver al Dashboard</Link>
            <div className="flex border-b mb-4">
                {TABS.map(tab => (
                    <button
                        key={tab}
                        onClick={() => setActiveTab(tab)}
                        className={`py-2 px-4 ${activeTab === tab ? 'border-b-2 border-blue-600 font-semibold text-blue-600' : 'text-gray-500'}`}
                    >
                        {tab}
                    </button>
                ))}
            </div>
            
            <div>
                {activeTab === 'Asistente IA' && <Chat lineId={lineId} />}
                {activeTab === 'Llamadas' && <EventTable columns={callColumns} data={details.calls} />}
                {activeTab === 'Textos' && <p>Tabla de textos no implementada.</p>}
                {activeTab === 'Datos' && <p>Tabla de datos no implementada.</p>}
            </div>
        </div>
    );
}