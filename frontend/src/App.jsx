import React, { useState, useEffect } from "react";
import { fetchModels, fetchHealth, sendChat, connectLogs } from "./api";
import LogPanel from "./components/LogPanel";
import ChatPanel from "./components/ChatPanel";
import SettingsPanel from "./components/SettingsPanel";

export default function App() {
    const [logs, setLogs] = useState([]);
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(false);
    const [models, setModels] = useState([]);
    const [gpu, setGpu] = useState(null);
    const [modelsLoading, setModelsLoading] = useState(false);
    const [theme, setTheme] = useState("light"); // Default to light mode

    const [config, setConfig] = useState({
        model: "",
        framework: "none",
        backend: "ollama",  // "ollama" | "gpustack"
        guardrails_ai: { pii: true, off_topic: true, jailbreak: true, hallucination: false, toxicity: true, competitor: false },
        nemo: { pii: true, off_topic: true, jailbreak: true, hallucination: true, toxicity: true, competitor: true },
        nemo_mode: "emb",  // "emb" | "qwen" | "hybrid"
        llama_guard: { S1: true, S2: true, S3: true, S4: true, S5: true, S6: true, S7: true, S8: true, S9: true, S10: true, S11: true, S12: true, S13: true },
    });

    // Toggle document theme class for index.css :root variables
    useEffect(() => {
        if (theme === "light") {
            document.documentElement.classList.add("light-mode");
        } else {
            document.documentElement.classList.remove("light-mode");
        }
    }, [theme]);

    // Re-fetch models & health when backend changes
    useEffect(() => {
        setModelsLoading(true);
        setModels([]); // clear old
        setGpu(null);  // clear old status

        Promise.all([
            fetchModels(config.backend),
            fetchHealth(config.backend)
        ]).then(([m, h]) => {
            setModels(m);
            if (m.length > 0) {
                // Keep selection if exists, else first
                setConfig((c) => ({ ...c, model: m.includes(c.model) ? c.model : m[0] }));
            } else {
                setConfig((c) => ({ ...c, model: "" }));
            }
            if (h) setGpu(h.gpu);
        }).finally(() => {
            setModelsLoading(false);
        });
    }, [config.backend]);

    useEffect(() => {
        const cleanup = connectLogs((log) => setLogs((prev) => [...prev, log]));
        return cleanup;
    }, []);

    const handleSend = async (text) => {
        setMessages((prev) => [...prev, { role: "user", content: text }]);
        setLoading(true);
        try {
            // Optimistic blocking check? No, server handles it.
            const res = await sendChat({ message: text, ...config });
            setMessages((prev) => [
                ...prev,
                {
                    role: "bot",
                    content: res.response,
                    blocked: res.blocked,
                    violation: res.violation_type,
                    framework: res.framework_used,
                },
            ]);
        } catch (err) {
            setMessages((prev) => [
                ...prev,
                { role: "bot", content: `Error: ${err.message}`, blocked: true, violation: "Server Error" },
            ]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="app">
            <SettingsPanel
                config={config}
                setConfig={setConfig}
                models={models}
                gpu={gpu}
                modelsLoading={modelsLoading}
                theme={theme}
                toggleTheme={() => setTheme(t => t === "dark" ? "light" : "dark")}
            />
            <ChatPanel messages={messages} onSend={handleSend} loading={loading} />
            <LogPanel logs={logs} onClear={() => setLogs([])} />
        </div>
    );
}
