import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

// Componente para una sola burbuja de chat, para mantener el código limpio.
const ChatBubble = ({ message }) => {
    return (
        <div className={`flex w-full mt-2 space-x-3 max-w-xs ${message.sender === 'user' ? 'ml-auto justify-end' : ''}`}>
            <div>
                <div className={`p-3 rounded-lg ${message.sender === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-900'}`}>
                    {/* Usamos 'whitespace-pre-wrap' para que el texto respete los saltos de línea y el formato que pueda venir de la IA */}
                    <p className="text-sm whitespace-pre-wrap">{message.text}</p>
                </div>
            </div>
        </div>
    );
};

// Componente principal del Chat
export default function Chat({ lineId }) {
    // Inicializa el chat con un mensaje de bienvenida de la IA
    const [messages, setMessages] = useState([
        { sender: 'ai', text: '¡Hola! Soy tu asistente de facturas. ¿Qué te gustaría saber sobre el uso de esta línea?' }
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    
    // Referencia al div que contiene los mensajes para poder hacer scroll
    const chatWindowRef = useRef(null);

    // Este efecto se ejecuta cada vez que el array de mensajes cambia.
    // Su única función es hacer scroll hasta el final para que el último mensaje sea visible.
    useEffect(() => {
        if (chatWindowRef.current) {
            chatWindowRef.current.scrollTop = chatWindowRef.current.scrollHeight;
        }
    }, [messages]);

    const handleSend = async () => {
        // No enviar si el input está vacío o solo contiene espacios
        if (!input.trim()) return;

        // Añadir el mensaje del usuario al historial de chat inmediatamente para una UX fluida
        const userMessage = { sender: 'user', text: input };
        setMessages(prev => [...prev, userMessage]);
        setInput(''); // Limpiar el campo de texto
        setIsLoading(true); // Activar el indicador de carga

        try {
            // Enviar la pregunta al backend
            const response = await axios.post('/api/query', {
                question: input,
                line_id: lineId
            });

            // Añadir la respuesta de la IA al historial de chat
            const aiMessage = { sender: 'ai', text: response.data.answer };
            setMessages(prev => [...prev, aiMessage]);

        } catch (error) {
            console.error("Error al contactar la API de consulta:", error);
            const errorMessage = { 
                sender: 'ai', 
                text: 'Lo siento, ha ocurrido un error al comunicarme con el servidor. Por favor, inténtalo de nuevo.' 
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false); // Desactivar el indicador de carga, tanto si hubo éxito como si no
        }
    };

    // Permite al usuario enviar el mensaje presionando la tecla "Enter"
    const handleKeyDown = (event) => {
        // Se envía con Enter, pero se puede hacer un salto de línea con Shift+Enter
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            handleSend();
        }
    };

    return (
        <div className="flex flex-col h-[60vh] bg-white rounded-lg shadow-md border">
            {/* Ventana de mensajes */}
            <div ref={chatWindowRef} className="flex-grow p-4 overflow-y-auto">
                {messages.map((msg, index) => (
                    <ChatBubble key={index} message={msg} />
                ))}
                {/* Indicador visual de que la IA está "pensando" */}
                {isLoading && (
                     <div className="flex w-full mt-2 space-x-3 max-w-xs">
                        <div>
                            <div className="bg-gray-200 p-3 rounded-lg">
                                <span className="animate-pulse text-sm">Pensando...</span>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Área de entrada de texto */}
            <div className="p-4 border-t bg-gray-50">
                <div className="flex items-center space-x-2">
                    <textarea
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        className="flex-grow p-2 border rounded-md resize-none focus:ring-2 focus:ring-blue-500 focus:outline-none"
                        placeholder="Ej: ¿Cuál fue la llamada más larga?"
                        rows="1"
                        disabled={isLoading}
                    />
                    <button 
                        onClick={handleSend} 
                        className="bg-blue-600 text-white font-semibold py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors" 
                        disabled={isLoading || !input.trim()}
                    >
                        Enviar
                    </button>
                </div>
            </div>
        </div>
    );
}