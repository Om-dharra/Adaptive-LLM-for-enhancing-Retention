'use-client';

import React, { useState } from 'react';
import api from '../lib/api';

const QuizModal = ({ onClose }) => {
    const [quizData, setQuizData] = useState(null);
    const [currentStep, setCurrentStep] = useState(0);
    const [score, setScore] = useState(0);
    const [finished, setFinished] = useState(false);

    // 1. Generate Quiz
    const loadQuiz = async () => {
        try {
            const res = await api.post('/quiz/generate');
            setQuizData(res.data);
        } catch (err) {
            alert("Failed to generate quiz. Try chatting more first!");
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
        await api.post('/quiz/submit', {
            topic_tag: quizData.topic,
            score: finalScore,
            total_questions: quizData.questions.length,
            attempts: 1
        });
        // The backend now automatically updates the Student Skill Index!
    };

    if (!quizData) return (
        <div className="p-8 text-center">
            <button onClick={loadQuiz} className="bg-purple-600 text-white px-6 py-2 rounded">
                Generate Micro-Quiz
            </button>
        </div>
    );

    if (finished) return (
        <div className="p-8 text-center bg-green-50 rounded">
            <h2 className="text-2xl font-bold mb-2">Quiz Complete!</h2>
            <p className="text-lg">You scored {score} / {quizData.questions.length}</p>
            <button onClick={onClose} className="mt-4 text-blue-600 underline">Back to Chat</button>
        </div>
    );

    const question = quizData.questions[currentStep];

    return (
        <div className="bg-white p-6 rounded-lg shadow-lg max-w-lg mx-auto mt-10">
            <h3 className="text-sm text-gray-500 uppercase tracking-wide mb-2">{quizData.topic}</h3>
            <h2 className="text-xl font-bold mb-6">{question.question_text}</h2>

            <div className="space-y-3">
                {question.options.map((opt) => (
                    <button
                        key={opt.id}
                        onClick={() => handleAnswer(opt.id)}
                        className="w-full text-left p-3 border rounded hover:bg-blue-50 transition"
                    >
                        <span className="font-bold mr-2">{opt.id}.</span> {opt.text}
                    </button>
                ))}
            </div>
            <div className="mt-4 text-right text-sm text-gray-400">
                Question {currentStep + 1} of {quizData.questions.length}
            </div>
        </div>
    );
};

export default QuizModal;