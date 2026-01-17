'use-client';

import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import { Send, User, Bot } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

import { useTelemetry } from '../hooks/useTelemetry';

const ChatInterface = ({ initialMessages, sessionId, onMessageSent }) => {
    const [input, setInput] = useState('');
    const [messages, setMessages] = useState(initialMessages);
    const [loading, setLoading] = useState(false);
    const [model, setModel] = useState("llama3");

    // Telemetry Hook
    const { handleCopy, handlePaste, startTimer, stopTimer, getAndResetMetrics } = useTelemetry();

    useEffect(() => {
        if (initialMessages) {
            setMessages(initialMessages);
        }
    }, [initialMessages]);

    // Send Message Function
    const handleSend = async () => {
        if (!input.trim()) return;

        // 1. Stop Reading Timer & Get Metrics
        stopTimer();
        const rawMetrics = getAndResetMetrics();

        // 2. Prepare features for XGBoost (Feature Engineering)
        const telemetryData = {
            tab_switch_count: rawMetrics.tab_switch_count,
            copy_paste_rate: rawMetrics.paste_count,
            time_to_query_ms: rawMetrics.time_to_query_ms,
            // Calculate reliance: Did they paste immediately?
            is_paste_heavy: rawMetrics.paste_count > 0 && input.length > 50
        };

        // Add user message to UI immediately
        const userMsg = { role: 'user', content: input };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setLoading(true);

        try {
            // Call your Backend
            const payload = {
                prompt: userMsg.content,
                model: model,
                telemetry_data: telemetryData // Send processed metrics
            };
            if (sessionId) payload.session_id = sessionId;

            const response = await api.post('/chat/message', payload);

            // Add AI response to UI
            const aiMsg = { role: 'ai', content: response.data.response };
            setMessages(prev => [...prev, aiMsg]);

            if (onMessageSent) onMessageSent();

            // 2. Start Reading Timer (User starts reading now)
            startTimer();

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
        <div
            className="flex flex-col h-[600px] border-none rounded-2xl bg-gradient-to-br from-indigo-50 to-purple-50 p-6 shadow-xl"
            onCopy={handleCopy}
        >
            {/* Header Area */}
            <div className="flex justify-between items-center mb-6 bg-white/50 p-3 rounded-xl backdrop-blur-sm">
                <div className="flex items-center gap-2">
                    <div className="bg-purple-100 p-2 rounded-full">
                        <Bot className="text-purple-600" size={24} />
                    </div>
                    <div>
                        <h3 className="font-bold text-gray-800 text-sm">AI Tutor</h3>
                        <p className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">Active</p>
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-500 font-medium">✨ Brain:</span>
                    <select
                        value={model}
                        onChange={(e) => setModel(e.target.value)}
                        className="text-xs border-none bg-white rounded-lg px-3 py-1.5 shadow-sm text-gray-600 focus:ring-2 focus:ring-purple-200 focus:outline-none cursor-pointer hover:bg-gray-50 transition"
                    >
                        <option value="gemini">Gemini Flash ⚡</option>
                        <option value="llama3">Llama 3 🦙</option>
                        <option value="deepseek">DeepSeek 🐋</option>
                    </select>
                </div>
            </div>

            {/* Chat Area */}
            <div className="flex-1 overflow-y-auto mb-4 space-y-6 pr-2 custom-scrollbar">
                {messages.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-full text-center text-gray-400 opacity-60">
                        <Bot size={48} className="mb-2 text-purple-200" />
                        <p className="text-sm">Say hello to start learning!</p>
                    </div>
                )}

                {messages.map((msg, idx) => (
                    <div key={idx} className={`flex w-full ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`flex max-w-[85%] ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'} items-end gap-2`}>
                            {/* Avatar */}
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 shadow-sm ${msg.role === 'user' ? 'bg-blue-100' : 'bg-purple-100'
                                }`}>
                                {msg.role === 'user' ?
                                    <User size={14} className="text-blue-600" /> :
                                    <Bot size={14} className="text-purple-600" />
                                }
                            </div>

                            {/* Bubble */}
                            <div className={`px-4 py-3 rounded-2xl shadow-sm border text-sm leading-relaxed ${msg.role === 'user'
                                ? 'bg-blue-600 text-white rounded-br-none border-blue-600'
                                : 'bg-white text-gray-700 rounded-bl-none border-gray-100'
                                }`}>
                                <div className={`prose prose-sm max-w-none ${msg.role === 'user' ? 'prose-invert' : ''}`}>
                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                        {msg.content}
                                    </ReactMarkdown>
                                </div>
                            </div>
                        </div>
                    </div>
                ))}

                {loading && (
                    <div className="flex justify-start w-full">
                        <div className="flex items-center gap-2 bg-white px-4 py-3 rounded-2xl rounded-bl-none shadow-sm border border-gray-100">
                            <div className="flex space-x-1">
                                <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                                <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                                <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                            </div>
                            <span className="text-xs text-gray-400 ml-2 font-medium">Thinking...</span>
                        </div>
                    </div>
                )}
            </div>

            {/* Input Area */}
            <div className="mt-2 bg-white p-2 rounded-xl shadow-lg border border-gray-100 flex items-center gap-2">
                <input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                    onPaste={handlePaste}
                    className="flex-1 p-3 bg-transparent text-gray-700 placeholder-gray-400 focus:outline-none text-sm"
                    placeholder="Type your question here..."
                />
                <button
                    onClick={handleSend}
                    disabled={!input.trim()}
                    className={`p-3 rounded-xl transition-all duration-200 ${input.trim()
                        ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md transform hover:scale-105 active:scale-95'
                        : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                        }`}
                >
                    <Send size={18} />
                </button>
            </div>
        </div>
    );
};

export default ChatInterface;