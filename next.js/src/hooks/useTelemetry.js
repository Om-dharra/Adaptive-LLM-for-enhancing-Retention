import { useState, useEffect, useRef } from 'react';
import toast from 'react-hot-toast';

export const useTelemetry = () => {
    const metrics = useRef({
        tab_switch_count: 0,
        copy_count: 0,
        paste_count: 0,
        time_to_query_ms: 0,
        start_reading_time: null,
    });

    useEffect(() => {
        const handleVisibilityChange = () => {
            if (document.hidden) {
                metrics.current.tab_switch_count += 1;
                console.log("Telemetry: Tab Switch Detected");
                toast('Tab Switch Detected!', {
                    icon: '👀',
                    style: {
                        borderRadius: '10px',
                        background: '#333',
                        color: '#fff',
                    },
                });
            }
        };

        document.addEventListener("visibilitychange", handleVisibilityChange);
        return () => document.removeEventListener("visibilitychange", handleVisibilityChange);
    }, []);

    const handleCopy = () => {
        metrics.current.copy_count += 1;
        toast('Text Copied! Your Dependency is Affecting.', {
            icon: '📋',
            style: {
                borderRadius: '10px',
                background: '#333',
                color: '#fff',
            },
        });
    };

    const handlePaste = () => {
        metrics.current.paste_count += 1;
        toast('Text Pasted! Your Dependency is Affecting.', {
            icon: '📝',
        });
    };

    const startTimer = () => {
        metrics.current.start_reading_time = Date.now();
    };

    const stopTimer = () => {
        if (metrics.current.start_reading_time) {
            const duration = Date.now() - metrics.current.start_reading_time;
            metrics.current.time_to_query_ms = duration;
        }
    };

    const getAndResetMetrics = () => {
        const data = { ...metrics.current };

        metrics.current.tab_switch_count = 0;
        metrics.current.copy_count = 0;
        metrics.current.paste_count = 0;
        metrics.current.time_to_query_ms = 0;
        metrics.current.start_reading_time = null;  // Wait for next AI response to start

        return data;
    };

    return {
        handleCopy,
        handlePaste,
        startTimer,
        stopTimer,
        getAndResetMetrics
    };
};
