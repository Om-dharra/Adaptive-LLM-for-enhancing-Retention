import React, { useEffect, useState } from 'react';
import api from '../lib/api';
import ChatInterface from '../components/ChatInterface';
import QuizModal from '../components/QuizModal';

const Dashboard = () => {
    const [user, setUser] = useState(null);

    useEffect(() => {
        // Fetch user profile (which includes skill_index and learning_path)
        api.get('/auth/me').then(res => setUser(res.data));
    }, []);

    if (!user) return <div>Loading Profile...</div>;

    return (
        <div className="min-h-screen bg-gray-100 p-8">
            <header className="mb-8 flex justify-between items-center">
                <h1 className="text-3xl font-bold text-gray-800">AI Adaptive Tutor</h1>
                <div className="text-right">
                    <p className="font-semibold">{user.username}</p>
                    <span className="text-sm text-gray-500">{user.email}</span>
                </div>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* LEFT COLUMN: Stats & Quiz */}
                <div className="space-y-6">
                    {/* Skill Index Card */}
                    <div className="bg-white p-6 rounded-lg shadow">
                        <h3 className="text-gray-500 text-sm font-bold uppercase mb-2">Your Skill Index</h3>
                        <div className="flex items-end gap-2">
                            <span className="text-5xl font-bold text-blue-600">
                                {user.skill_index?.index_value ? Number(user.skill_index.index_value).toFixed(1) : 50}
                            </span>
                            <span className="text-gray-400 mb-2">/ 100</span>
                        </div>
                        <div className="mt-4 p-2 bg-blue-50 text-blue-800 rounded text-center text-sm font-semibold">
                            Current Level: {user.skill_index?.bucket || "Moderate"}
                        </div>
                    </div>

                    {/* Learning Path Card */}
                    <div className="bg-white p-6 rounded-lg shadow">
                        <h3 className="text-gray-500 text-sm font-bold uppercase mb-2">Active Learning Path</h3>
                        <p className="text-lg font-medium">
                            {user.learning_path?.path_type || "Balanced"}
                        </p>
                        <p className="text-xs text-gray-400 mt-1">
                            AI Persona: {user.learning_path?.ai_persona_mode || "Tutor"}
                        </p>
                    </div>

                    {/* Quiz Trigger */}
                    <QuizModal onClose={() => console.log("Quiz Closed")} />
                </div>

                {/* RIGHT COLUMN: Chat */}
                <div className="lg:col-span-2">
                    <ChatInterface />
                </div>
            </div>
        </div>
    );
};

export default Dashboard;