import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../lib/api';

const Register = () => {
    const [formData, setFormData] = useState({
        username: '',
        email: '',
        password: ''
    });
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        try {
            // Matches the UserCreateRequest schema in your backend
            await api.post('/auth/', {
                username: formData.username,
                email: formData.email,
                password: formData.password
            });

            alert("Registration successful! Please log in.");
            navigate('/'); // Redirect to Login
        } catch (err) {
            console.error(err);
            // Display error message from backend if available
            setError(err.response?.data?.detail || "Registration failed. Try a different username.");
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-100">
            <div className="bg-white p-8 rounded-lg shadow-md w-96">
                <h2 className="text-2xl font-bold mb-6 text-center text-blue-600">Create Account</h2>

                {error && <div className="bg-red-100 text-red-700 p-2 rounded mb-4 text-sm">{error}</div>}

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Username</label>
                        <input
                            type="text" name="username" required
                            className="w-full mt-1 p-2 border rounded focus:ring-2 focus:ring-blue-500 outline-none"
                            onChange={handleChange}
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Email</label>
                        <input
                            type="email" name="email" required
                            className="w-full mt-1 p-2 border rounded focus:ring-2 focus:ring-blue-500 outline-none"
                            onChange={handleChange}
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Password</label>
                        <input
                            type="password" name="password" required
                            className="w-full mt-1 p-2 border rounded focus:ring-2 focus:ring-blue-500 outline-none"
                            onChange={handleChange}
                        />
                    </div>

                    <button type="submit" className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 transition">
                        Register
                    </button>
                </form>

                <p className="mt-4 text-center text-sm text-gray-600">
                    Already have an account? <Link to="/" className="text-blue-600 hover:underline">Log in</Link>
                </p>
            </div>
        </div>
    );
};

export default Register;