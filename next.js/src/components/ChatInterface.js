'use-client';

import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import { Send, User, Bot } from 'lucide-react';

const ChatInterface = ({ initialMessages, sessionId }) => {
    const [input, setInput] = useState('');
    const [messages, setMessages] = useState(initialMessages);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (initialMessages) {
            setMessages(initialMessages);
        }
    }, [initialMessages]);

    // Send Message Function
    const handleSend = async () => {
        if (!input.trim()) return;

        // Add user message to UI immediately
        const userMsg = { role: 'user', content: input };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setLoading(true);

        try {
            // Call your Backend
            const payload = { prompt: userMsg.content };
            if (sessionId) payload.session_id = sessionId;

            const response = await api.post('/chat/message', payload);

            // Add AI response to UI
            const aiMsg = { role: 'ai', content: response.data.response };
            setMessages(prev => [...prev, aiMsg]);

            // OPTIONAL: Check if backend flagged a "Struggle" (if you return that flag)
            // You could show a "Don't give up!" toast notification here.

        } catch (error) {
            console.error("Chat Error:", error);
            setMessages(prev => [...prev, { role: 'system', content: "Error connecting to Tutor." }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-[600px] border rounded-lg bg-gray-50 p-4">
            <div className="flex-1 overflow-y-auto mb-4 space-y-4">
                {messages.map((msg, idx) => (
                    <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[80%] p-3 rounded-lg ${msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-white border shadow-sm'}`}>
                            <div className="flex items-center gap-2 mb-1 text-xs opacity-70">
                                {msg.role === 'user' ? <User size={12} /> : <Bot size={12} />}
                                <span>{msg.role === 'user' ? 'You' : 'AI Tutor'}</span>
                            </div>
                            <p className="whitespace-pre-wrap">{msg.content}</p>
                        </div>
                    </div>
                ))}
                {loading && <div className="text-center text-gray-400 animate-pulse">Thinking...</div>}
            </div>

            <div className="flex gap-2">
                <input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                    className="flex-1 p-2 border rounded"
                    placeholder="Ask a question..."
                />
                <button onClick={handleSend} className="bg-blue-600 text-white p-2 rounded hover:bg-blue-700">
                    <Send size={20} />
                </button>
            </div>
        </div>
    );
};

export default ChatInterface;