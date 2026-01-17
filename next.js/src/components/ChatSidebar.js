'use client';

import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { MessageSquare, Clock, ChevronLeft, ChevronRight, PlusCircle, Trash2 } from 'lucide-react';

export default function ChatSidebar({ onSelectSession, onNewChat }) {
    const [sessions, setSessions] = useState([]);
    const [isOpen, setIsOpen] = useState(true);
    const [selectedId, setSelectedId] = useState(null);

    // Fetch sessions on load
    const fetchSessions = async () => {
        try {
            const res = await api.get('/chat/sessions');
            setSessions(res.data);
        } catch (err) {
            console.error("Failed to load sessions", err);
        }
    };

    useEffect(() => {
        fetchSessions();
    }, []);

    // Helper to format date nicely
    const formatDate = (dateString) => {
        if (!dateString) return '';
        const date = new Date(dateString);
        return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    };

    const handleSelect = (session) => {
        setSelectedId(session.session_id);
        onSelectSession(session.session_id);
    };

    const handleNewChat = () => {
        setSelectedId(null);
        onNewChat();
    };

    const handleDeleteSession = async (e, sessionId) => {
        e.stopPropagation();
        if (!confirm("Are you sure you want to delete this chat?")) return;

        try {
            await api.delete(`/chat/sessions/${sessionId}`);
            setSessions(prev => prev.filter(s => s.session_id !== sessionId));
            if (selectedId === sessionId) {
                handleNewChat();
            }
        } catch (err) {
            console.error("Failed to delete", err);
        }
    };

    if (!isOpen) {
        return (
            <button
                onClick={() => setIsOpen(true)}
                className="fixed left-0 top-24 bg-white p-2 border-r shadow-md rounded-r-lg z-10"
            >
                <ChevronRight size={20} />
            </button>
        );
    }

    return (
        <div className="w-80 bg-white/80 backdrop-blur-md border-r h-[600px] flex flex-col shadow-sm transition-all duration-300 rounded-l-2xl">
            {/* Header */}
            <div className="p-5 border-b border-gray-100 flex justify-between items-center bg-gray-50/50 rounded-tl-2xl">
                <h2 className="font-bold text-gray-800 flex items-center gap-2">
                    <div className="bg-indigo-100 p-1.5 rounded-lg text-indigo-600">
                        <Clock size={16} />
                    </div>
                    History
                </h2>
                <button onClick={() => setIsOpen(false)} className="text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 p-1 rounded-lg transition">
                    <ChevronLeft size={20} />
                </button>
            </div>

            {/* New Chat Button */}
            <div className="p-4">
                <button
                    onClick={handleNewChat}
                    className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-indigo-500 to-purple-600 text-white py-3 rounded-xl font-semibold shadow-md hover:shadow-lg transform hover:-translate-y-0.5 transition-all duration-200"
                >
                    <PlusCircle size={18} /> New Session
                </button>
            </div>

            {/* Session List */}
            <div className="flex-1 overflow-y-auto px-3 pb-3 space-y-2 custom-scrollbar">
                {sessions.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-40 text-gray-300 mt-10 text-center">
                        <MessageSquare size={32} className="mb-2 opacity-50" />
                        <span className="text-sm">No chats yet.<br />Start a new journey! 🚀</span>
                    </div>
                ) : (
                    sessions.map((session) => (
                        <div
                            key={session.session_id}
                            onClick={() => handleSelect(session)}
                            className={`group relative p-3 rounded-xl cursor-pointer border transition-all duration-200 ${selectedId === session.session_id
                                    ? 'bg-indigo-50 border-indigo-200 shadow-sm'
                                    : 'bg-white border-transparent hover:bg-gray-50 hover:border-gray-200'
                                }`}
                        >
                            <div className="flex justify-between items-start mb-1">
                                <p className={`text-sm font-semibold truncate w-[85%] ${selectedId === session.session_id ? 'text-indigo-900' : 'text-gray-700'}`}>
                                    {session.title || "Untitled Session"}
                                </p>
                                {selectedId === session.session_id && <div className="w-2 h-2 rounded-full bg-indigo-500 mt-1.5"></div>}
                            </div>

                            <div className="flex justify-between items-center mt-2">
                                <span className="text-[10px] font-medium text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">
                                    {formatDate(session.last_updated)}
                                </span>
                            </div>

                            <button
                                onClick={(e) => handleDeleteSession(e, session.session_id)}
                                className="absolute bottom-3 right-3 text-gray-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all p-1.5 hover:bg-red-50 rounded-lg"
                                title="Delete Chat"
                            >
                                <Trash2 size={14} />
                            </button>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
