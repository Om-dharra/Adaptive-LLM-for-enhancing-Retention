'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import api from '@/lib/api';

export default function RegisterPage() {
    const [formData, setFormData] = useState({ username: '', email: '', password: '' });
    const [error, setError] = useState('');
    const router = useRouter();

    const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await api.post('/auth/', formData);
            alert("Registration successful! Please log in.");
            router.push('/');
        } catch (err) {
            setError(err.response?.data?.detail || "Registration failed.");
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-100">
            <div className="bg-white p-8 rounded-lg shadow-md w-96">
                <h2 className="text-2xl font-bold mb-6 text-center text-blue-600">Create Account</h2>
                {error && <div className="bg-red-100 text-red-700 p-2 rounded mb-4 text-sm">{error}</div>}
                <form onSubmit={handleSubmit} className="space-y-4">
                    <input name="username" placeholder="Username" onChange={handleChange} className="w-full p-2 border rounded text-black" required />
                    <input name="email" type="email" placeholder="Email" onChange={handleChange} className="w-full p-2 border rounded text-black" required />
                    <input name="password" type="password" placeholder="Password" onChange={handleChange} className="w-full p-2 border rounded text-black" required />
                    <button type="submit" className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700">Register</button>
                </form>
                <p className="mt-4 text-center text-sm text-gray-600">
                    Already have an account? <Link href="/" className="text-blue-600 hover:underline">Log in</Link>
                </p>
            </div>
        </div>
    );
}