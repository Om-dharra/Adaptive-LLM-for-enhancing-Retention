import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';
import api from '../lib/api';

const AnalyticsDashboard = () => {
    const [retentionData, setRetentionData] = useState([]);
    const [weaknessData, setWeaknessData] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [retRes, weakRes] = await Promise.all([
                    api.get('/analytics/retention'),
                    api.get('/analytics/weaknesses')
                ]);
                setRetentionData(retRes.data);
                setWeaknessData(weakRes.data);
            } catch (error) {
                console.error("Failed to load analytics", error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    if (loading) return <div className="p-4 text-xs text-gray-500">Loading Insights...</div>;

    // Get unique topics for Lines in Retention Chart (if user wants 1 line per topic)
    // For simplicity, we might just plot the raw data points if structured correctly by backend.
    // Our backend returns [{ date: '...', 'TopicA': 80, 'TopicB': 50 }]

    // Extract keys that aren't 'date' to know which lines to draw
    const topicKeys = retentionData.length > 0
        ? Object.keys(retentionData[0]).filter(k => k !== 'date')
        : [];

    const colors = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#0088fe'];

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">

            {/* 1. Retention Curve (Line Chart) */}
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                <h3 className="font-bold text-gray-700 mb-4 flex items-center gap-2">
                    📉 Forgetting Curve (Retention)
                </h3>
                <div className="h-64">
                    {retentionData.length === 0 ? (
                        <div className="flex items-center justify-center h-full text-gray-400 text-sm">No quiz history yet.</div>
                    ) : (
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={retentionData}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                                <XAxis dataKey="date" fontSize={12} stroke="#9ca3af" />
                                <YAxis domain={[0, 100]} fontSize={12} stroke="#9ca3af" />
                                <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                                <Legend wrapperStyle={{ fontSize: '12px' }} />
                                {topicKeys.map((topic, index) => (
                                    <Line
                                        key={topic}
                                        type="monotone"
                                        dataKey={topic}
                                        stroke={colors[index % colors.length]}
                                        strokeWidth={2}
                                        dot={{ r: 4 }}
                                        activeDot={{ r: 6 }}
                                    />
                                ))}
                            </LineChart>
                        </ResponsiveContainer>
                    )}
                </div>
            </div>

            {/* 2. Weakness Heatmap (Bar Chart) */}
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                <h3 className="font-bold text-gray-700 mb-4 flex items-center gap-2">
                    🌡️ Weakness Heatmap
                </h3>
                <div className="h-64">
                    {weaknessData.length === 0 ? (
                        <div className="flex items-center justify-center h-full text-gray-400 text-sm">No weak areas found.</div>
                    ) : (
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={weaknessData} layout="vertical">
                                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                                <XAxis type="number" domain={[0, 100]} hide />
                                <YAxis dataKey="topic" type="category" width={100} fontSize={12} stroke="#4b5563" />
                                <Tooltip cursor={{ fill: 'transparent' }} />
                                <Bar dataKey="score" radius={[0, 4, 4, 0]}>
                                    {weaknessData.map((entry, index) => (
                                        <cell key={`cell-${index}`} fill={entry.score < 50 ? '#ef4444' : (entry.score < 75 ? '#eab308' : '#22c55e')} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    )}
                </div>
            </div>

        </div>
    );
};

export default AnalyticsDashboard;
