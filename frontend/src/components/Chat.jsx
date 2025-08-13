import React, { useState } from 'react';
import axios from 'axios';

export default function Chat({ lineId }) {
    const [question, setQuestion] = useState('');
    const [messages, setMessages] = useState([]);
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!question.trim()) return;

        const userMessage = { type: 'user', content: question };
        setMessages(prev => [...prev, userMessage]);
        setIsLoading(true);
        setQuestion('');

        try {
            const response = await axios.post('/api/query', {
                question: question,
                line_id: parseInt(lineId)
            });
            
            const aiMessage = { type: 'ai', content: response.data.answer };
            setMessages(prev => [...prev, aiMessage]);
        } catch (error) {
            const errorMessage = { 
                type: 'error', 
                content: error.response?.data?.error || 'Error al comunicarse con la IA' 
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="bg-white rounded-lg shadow-md p-6">
            <div className="h-96 overflow-y-auto mb-4 border rounded p-4 bg-gray-50">
                {messages.length === 0 ? (
                    <p className="text-gray-500 text-center">Pregúntame cualquier cosa sobre esta línea telefónica</p>
                ) : (
                    messages.map((msg, idx) => (
                        <div key={idx} className={`mb-3 ${msg.type === 'user' ? 'text-right' : 'text-left'}`}>
                            <div className={`inline-block max-w-[80%] p-3 rounded-lg ${
                                msg.type === 'user' ? 'bg-blue-600 text-white' :
                                msg.type === 'error' ? 'bg-red-100 text-red-700' :
                                'bg-gray-200 text-gray-800'
                            }`}>
                                {msg.content}
                            </div>
                        </div>
                    ))
                )}
                {isLoading && (
                    <div className="text-left">
                        <div className="inline-block bg-gray-200 text-gray-800 p-3 rounded-lg">
                            Pensando...
                        </div>
                    </div>
                )}
            </div>
            <form onSubmit={handleSubmit} className="flex gap-2">
                <input
                    type="text"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="Escribe tu pregunta..."
                    className="flex-1 border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    disabled={isLoading}
                />
                <button
                    type="submit"
                    disabled={isLoading || !question.trim()}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                >
                    Enviar
                </button>
            </form>
        </div>
    );
}