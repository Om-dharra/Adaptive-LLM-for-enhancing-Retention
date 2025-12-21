'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import ChatInterface from '@/components/ChatInterface';
import ChatSidebar from '@/components/ChatSidebar';
import AnalyticsDashboard from '@/components/AnalyticsDashboard';

export default function DashboardPage() {
    const [user, setUser] = useState(null);
    const router = useRouter();
    const [chatContext, setChatContext] = useState([]);
    const [sessionId, setSessionId] = useState(null);


    const fetchUser = () => {
        const token = localStorage.getItem('token');
        if (!token) {
            router.push('/');
            return;
        }
        api.get('/auth/me')
            .then(res => setUser(res.data))
            .catch(() => {
                localStorage.removeItem('token');
                router.push('/');
            });
    };

    useEffect(() => {
        fetchUser();
    }, [router]);


    const handleSelectSession = async (id) => {
        setSessionId(id);
        setChatContext([]); // Clear while loading
        try {
            const res = await api.get(`/chat/history/${id}`);
            const formatted = res.data.map(item => [
                { role: 'user', content: item.prompt },
                { role: 'ai', content: item.response }
            ]).flat();
            setChatContext(formatted);
        } catch (err) {
            console.error("Failed to load session history", err);
        }
    };

    const handleNewChat = () => {
        setSessionId(null);
        setChatContext([]);
    };
    if (!user) return <div className="p-8 text-center">Loading Profile...</div>;

    return (
        <div className="min-h-screen bg-gray-100 p-6">
            <header className="mb-6 flex justify-between items-center bg-white p-4 rounded-lg shadow-sm">
                <h1 className="text-2xl font-bold text-gray-800">AI Adaptive Tutor</h1>
                <div className="text-right">
                    <p className="font-semibold text-black">{user.username}</p>
                    <span className="text-xs text-gray-500 uppercase tracking-wider">
                        {user.skill_index?.bucket || "Moderate"} Learner
                    </span>
                </div>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">

                {/* LEFT: Stats & Quiz (Takes 1 column) */}
                <div className="space-y-6 lg:col-span-1">
                    <div className="bg-white p-6 rounded-lg shadow-sm border-t-4 border-blue-500">
                        <h3 className="text-gray-400 text-xs font-bold uppercase mb-1">Skill Index</h3>
                        <div className="text-4xl font-bold text-gray-800">
                            {user.skill_index?.index_value ? Number(user.skill_index.index_value).toFixed(1) : 50}
                        </div>
                        <div className="mt-2 text-xs text-gray-500">
                            Path: <span className="font-medium text-blue-600">{user.learning_path?.path_type}</span>
                        </div>
                    </div>

                    {/* Quiz CTA */}
                    <div className="bg-gradient-to-br from-purple-600 to-indigo-700 p-6 rounded-lg shadow-sm text-white relative overflow-hidden group cursor-pointer" onClick={() => router.push(sessionId ? `/quiz?session_id=${sessionId}` : '/quiz')}>
                        {/* Decorative circle */}
                        <div className="absolute top-[-20px] right-[-20px] w-24 h-24 bg-white opacity-10 rounded-full group-hover:scale-125 transition-transform"></div>

                        <h3 className="font-bold text-lg mb-1 relative z-10">Verify Skills</h3>
                        <p className="text-indigo-100 text-xs mb-4 relative z-10">
                            Take a quick micro-quiz to update your adaptive profile.
                        </p>
                        <button
                            className="w-full bg-white text-indigo-700 py-2 rounded text-sm font-bold shadow hover:bg-gray-50 transition"
                        >
                            Start Quiz
                        </button>
                    </div>
                </div>

                {/* RIGHT: Chat Area with Sidebar (Takes 3 columns) */}
                <div className="lg:col-span-3 flex bg-white rounded-lg shadow-sm overflow-hidden h-[600px]">
                    {/* New Sidebar Component */}
                    <ChatSidebar onSelectSession={handleSelectSession} onNewChat={handleNewChat} />

                    {/* Chat Interface fills the remaining space */}
                    <div className="flex-1">
                        <ChatInterface initialMessages={chatContext} sessionId={sessionId} onMessageSent={fetchUser} />
                    </div>
                </div>

            </div>

            {/* Analytics Section */}
            <AnalyticsDashboard />

        </div>
    );
}