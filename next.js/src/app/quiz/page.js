'use client';

import React, { useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import api from '@/lib/api';
import { ArrowLeft, CheckCircle, AlertCircle } from 'lucide-react';

export default function QuizPage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const sessionId = searchParams.get('session_id');

    const [quizData, setQuizData] = useState(null);
    const [currentStep, setCurrentStep] = useState(0);
    const [score, setScore] = useState(0);
    const [finished, setFinished] = useState(false);
    const [loading, setLoading] = useState(false);

    // 1. Generate Quiz
    const loadQuiz = async () => {
        setLoading(true);
        try {
            const payload = sessionId ? { session_id: sessionId } : {};
            const res = await api.post('/quiz/generate', payload);
            setQuizData(res.data);
        } catch (err) {
            alert("Failed to generate quiz. Try chatting more first!");
        } finally {
            setLoading(false);
        }
    };

    // 2. Handle Answer
    const handleAnswer = (optionId) => {
        const question = quizData.questions[currentStep];
        if (optionId === question.correct_option_id) {
            setScore(prev => prev + 1);
        }

        if (currentStep < quizData.questions.length - 1) {
            setCurrentStep(prev => prev + 1);
        } else {
            submitResults(score + (optionId === question.correct_option_id ? 1 : 0));
        }
    };

    // 3. Submit Score & Trigger Adaptive Engine
    const submitResults = async (finalScore) => {
        setFinished(true);
        try {
            await api.post('/quiz/submit', {
                topic_tag: quizData.topic,
                score: finalScore,
                total_questions: quizData.questions.length,
                attempts: 1
            });
        } catch (err) {
            console.error("Failed to submit score", err);
        }
    };

    const handleBack = () => {
        router.push('/dashboard');
    };

    if (loading) return (
        <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
            <p className="text-gray-600">Generating your personalized verification quiz...</p>
        </div>
    );

    if (!quizData) return (
        <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
            <div className="bg-white p-8 rounded-xl shadow-lg text-center max-w-md w-full">
                <div className="bg-blue-100 p-4 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-6">
                    <CheckCircle className="text-blue-600" size={32} />
                </div>
                <h1 className="text-2xl font-bold text-gray-800 mb-2">Ready to Verify?</h1>
                <p className="text-gray-500 mb-8">
                    Based on your recent chat history, we'll generate a quick Micro-Quiz to check your understanding.
                </p>
                <div className="space-y-3">
                    <button
                        onClick={loadQuiz}
                        className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition shadow-md"
                    >
                        Start Micro-Quiz
                    </button>
                    <button
                        onClick={handleBack}
                        className="w-full bg-white border border-gray-300 text-gray-700 py-3 rounded-lg font-medium hover:bg-gray-50 transition"
                    >
                        Back to Dashboard
                    </button>
                </div>
            </div>
        </div>
    );

    if (finished) return (
        <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
            <div className="bg-white p-8 rounded-xl shadow-lg text-center max-w-md w-full">
                <div className="bg-green-100 p-4 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-6">
                    <CheckCircle className="text-green-600" size={32} />
                </div>
                <h2 className="text-2xl font-bold mb-2">Quiz Complete!</h2>
                <div className="text-5xl font-bold text-blue-600 mb-2">
                    {Math.round((score / quizData.questions.length) * 100)}%
                </div>
                <p className="text-gray-500 mb-8">
                    You scored {score} out of {quizData.questions.length} questions.
                </p>
                <button
                    onClick={handleBack}
                    className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition shadow-md"
                >
                    Return to Dashboard
                </button>
            </div>
        </div>
    );

    const question = quizData.questions[currentStep];

    return (
        <div className="min-h-screen bg-gray-100 flex flex-col items-center py-10 px-4">
            <div className="w-full max-w-2xl">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <button
                        onClick={handleBack}
                        className="flex items-center text-gray-500 hover:text-gray-800 transition"
                    >
                        <ArrowLeft size={20} className="mr-2" /> Exit
                    </button>
                    <div className="text-sm font-semibold text-gray-500 uppercase tracking-wide">
                        {quizData.topic}
                    </div>
                </div>

                {/* Progress Bar */}
                <div className="w-full bg-gray-200 rounded-full h-2 mb-6">
                    <div
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${((currentStep + 1) / quizData.questions.length) * 100}%` }}
                    ></div>
                </div>

                {/* Question Card */}
                <div className="bg-white p-8 rounded-xl shadow-lg">
                    <div className="flex justify-between items-start mb-6">
                        <h2 className="text-xl font-bold text-gray-800 leading-relaxed">
                            {question.question_text}
                        </h2>
                        <span className="bg-blue-50 text-blue-800 text-xs font-bold px-2 py-1 rounded">
                            Q{currentStep + 1}
                        </span>
                    </div>

                    <div className="space-y-3">
                        {question.options.map((opt) => (
                            <button
                                key={opt.id}
                                onClick={() => handleAnswer(opt.id)}
                                className="w-full text-left p-4 border-2 border-gray-100 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all group"
                            >
                                <div className="flex items-center">
                                    <span className="w-8 h-8 rounded-full bg-gray-100 text-gray-500 flex items-center justify-center font-bold mr-4 group-hover:bg-blue-500 group-hover:text-white transition-colors">
                                        {opt.id}
                                    </span>
                                    <span className="font-medium text-gray-700 group-hover:text-blue-900">
                                        {opt.text}
                                    </span>
                                </div>
                            </button>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
