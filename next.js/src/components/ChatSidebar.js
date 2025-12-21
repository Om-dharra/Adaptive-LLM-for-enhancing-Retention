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
        <div className="w-80 bg-white border-r h-[600px] flex flex-col shadow-sm transition-all duration-300">
            {/* Header */}
            <div className="p-4 border-b flex justify-between items-center">
                <h2 className="font-bold text-gray-700 flex items-center gap-2">
                    <Clock size={18} /> Chats
                </h2>
                <button onClick={() => setIsOpen(false)} className="text-gray-400 hover:text-gray-600">
                    <ChevronLeft size={20} />
                </button>
            </div>

            {/* New Chat Button */}
            <div className="p-3">
                <button
                    onClick={handleNewChat}
                    className="w-full flex items-center justify-center gap-2 bg-blue-600 text-white py-2 rounded-lg font-medium hover:bg-blue-700 transition"
                >
                    <PlusCircle size={18} /> New Chat
                </button>
            </div>

            {/* Session List */}
            <div className="flex-1 overflow-y-auto p-2 space-y-2">
                {sessions.length === 0 ? (
                    <div className="text-center text-gray-400 mt-10 text-sm">No chats yet.</div>
                ) : (
                    sessions.map((session) => (
                        <div
                            key={session.session_id}
                            onClick={() => handleSelect(session)}
                            className={`group relative p-3 rounded-lg cursor-pointer border transition ${selectedId === session.session_id
                                ? 'bg-blue-50 border-blue-200'
                                : 'hover:bg-gray-50 border-transparent hover:border-gray-200'
                                }`}
                        >
                            <p className={`text-sm font-medium truncate pr-6 ${selectedId === session.session_id ? 'text-blue-800' : 'text-gray-800'
                                }`}>
                                {session.title}
                            </p>

                            <div className="flex justify-between items-center mt-1">
                                <span className="text-xs text-gray-400">{formatDate(session.last_updated)}</span>
                                <MessageSquare size={12} className={
                                    selectedId === session.session_id ? 'text-blue-400' : 'text-gray-300'
                                } />
                            </div>

                            <button
                                onClick={(e) => handleDeleteSession(e, session.session_id)}
                                className="absolute top-3 right-2 text-gray-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity p-1"
                                title="Delete Chat"
                            >
                                <Trash2 size={16} />
                            </button>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
