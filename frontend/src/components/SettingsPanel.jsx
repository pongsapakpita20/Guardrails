import React from "react";

function Toggle({ checked, onChange }) {
    return (
        <label className="toggle">
            <input type="checkbox" checked={checked} onChange={onChange} />
            <span className="track" />
        </label>
    );
}

const FRAMEWORK_GUARDS = {
    none: { label: "None (Raw Model)", guards: [] },
    guardrails_ai: { label: "Guardrails AI", guards: ["pii", "off_topic", "jailbreak", "hallucination", "toxicity", "competitor"] },
    nemo: { label: "NeMo Guardrails", guards: ["pii", "off_topic", "jailbreak", "hallucination", "toxicity", "competitor"] },
    llama_guard: { label: "Llama Guard 3 8B", guards: [] },
};

// ===== Input Guards (3) =====
const INPUT_GUARDS = [
    { key: "pii", emoji: "🔒", label: "PII Detection" },
    { key: "off_topic", emoji: "🎯", label: "Off-Topic" },
    { key: "jailbreak", emoji: "🛡️", label: "Jailbreak Attempt" },
];

// ===== Output Guards (3) =====
const OUTPUT_GUARDS = [
    { key: "hallucination", emoji: "🌀", label: "Hallucination" },
    { key: "toxicity", emoji: "⚠️", label: "Profanity & Toxicity" },
    { key: "competitor", emoji: "🏢", label: "Competitor Mention" },
];

const LLAMA_CATEGORIES = [
    { key: "S1", label: "Violent Crimes" },
    { key: "S2", label: "Non-Violent Crimes" },
    { key: "S3", label: "Sex Crimes" },
    { key: "S4", label: "Child Exploitation" },
    { key: "S5", label: "Defamation" },
    { key: "S6", label: "Specialized Advice" },
    { key: "S7", label: "Privacy" },
    { key: "S8", label: "Intellectual Property" },
    { key: "S9", label: "Indiscriminate Weapons" },
    { key: "S10", label: "Hate" },
    { key: "S11", label: "Self-Harm" },
    { key: "S12", label: "Sexual Content" },
    { key: "S13", label: "Elections" },
    { key: "S14", label: "Competitor Mention (คู่แข่ง)" },
    { key: "S15", label: "Off-Topic (นอกเรื่อง)" },
    { key: "S16", label: "Profanity & Toxicity (คำหยาบ)" },
];

export default function SettingsPanel({ config, setConfig, models, gpu, modelsLoading, theme, toggleTheme }) {
    const fw = config.framework;
    const fwInfo = FRAMEWORK_GUARDS[fw] || FRAMEWORK_GUARDS.none;
    const fwToggles = config[fw] || {};

    const setModel = (v) => setConfig((c) => ({ ...c, model: v }));
    const setFramework = (v) => setConfig((c) => ({ ...c, framework: v }));
    const setBackend = (v) => setConfig((c) => ({ ...c, backend: v }));

    const toggleGuard = (guardKey) => {
        setConfig((c) => ({
            ...c,
            [fw]: { ...c[fw], [guardKey]: !c[fw]?.[guardKey] },
        }));
    };

    // Filter which input/output guards this framework supports
    const inputGuards = INPUT_GUARDS.filter(g => fwInfo.guards.includes(g.key));
    const outputGuards = OUTPUT_GUARDS.filter(g => fwInfo.guards.includes(g.key));

    return (
        <div className="panel settings-panel">
            <div className="panel-header">
                <h2>
                    <span className="icon">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
                    </span>
                    Settings
                </h2>
            </div>

            <div className="panel-body">
                {/* Theme Toggle */}
                <div className="settings-section">
                    <div className="setting-row">
                        <span>Appearance ({theme === "dark" ? "Dark" : "Light"})</span>
                        <Toggle checked={theme === "light"} onChange={toggleTheme} />
                    </div>
                </div>

                {/* System Status Section */}
                <div className="settings-section">
                    <h3>System Status</h3>
                    {modelsLoading ? (
                        <div className="gpu-badge offline">Checking...</div>
                    ) : gpu ? (
                        <div className={`gpu-badge ${gpu.cuda_available ? "online" : "offline"}`}>
                            {gpu.cuda_available ? gpu.gpu_name : "CPU Only"}
                        </div>
                    ) : (
                        <div className="gpu-badge offline">Offline</div>
                    )}
                </div>

                {/* Backend selection */}
                <div className="settings-section">
                    <h3>Inference Backend</h3>
                    <div className="backend-switcher">
                        <button
                            className={`backend-btn ${config.backend === "ollama" ? "active" : ""}`}
                            onClick={() => setBackend("ollama")}
                        >
                            Ollama
                        </button>
                        <button
                            className={`backend-btn ${config.backend === "gpustack" ? "active" : ""}`}
                            onClick={() => setBackend("gpustack")}
                        >
                            GPUStack
                        </button>
                    </div>
                </div>

                {/* Model */}
                <div className="settings-section">
                    <h3>Model ({config.backend === "gpustack" ? "GPUStack" : "Ollama"})</h3>
                    <div className="select-wrap">
                        <select value={config.model} onChange={(e) => setModel(e.target.value)} disabled={modelsLoading}>
                            {modelsLoading && <option>⏳ Loading...</option>}
                            {!modelsLoading && models.length === 0 && <option>ไม่พบ Model</option>}
                            {!modelsLoading && models.map((m) => <option key={m} value={m}>{m}</option>)}
                        </select>
                    </div>
                </div>

                {/* Framework */}
                <div className="settings-section">
                    <h3>Guardrail Framework</h3>
                    <div className="select-wrap">
                        <select value={fw} onChange={(e) => setFramework(e.target.value)}>
                            {Object.entries(FRAMEWORK_GUARDS).map(([key, v]) => (
                                <option key={key} value={key}>{v.label}</option>
                            ))}
                        </select>
                    </div>
                </div>

                {/* NeMo Mode Selection */}
                {fw === "nemo" && (
                    <div className="settings-section">
                        <h3>NeMo Mode</h3>
                        <div className="select-wrap">
                            <select
                                value={config.nemo_mode || "emb"}
                                onChange={(e) => setConfig((c) => ({ ...c, nemo_mode: e.target.value }))}
                            >
                                <option value="emb">Embedding-only (Fast ~50ms)</option>
                                <option value="qwen">Qwen 3 0.6B Guard (LLM ~2-5s)</option>
                                <option value="hybrid">Hybrid (Embedding → Qwen)</option>
                            </select>
                        </div>
                        <p style={{ fontSize: "0.85em", color: "var(--text-secondary)", marginTop: "0.5em" }}>
                            {config.nemo_mode === "emb" && "ใช้ embedding matching เท่านั้น (เร็วที่สุด)"}
                            {config.nemo_mode === "qwen" && "ใช้ Qwen 3 0.6B เป็น LLM guard (แม่นยำกว่า)"}
                            {config.nemo_mode === "hybrid" && "ตรวจด้วย Embedding ก่อน แล้วค่อยตรวจด้วย Qwen ถ้าผ่าน"}
                        </p>
                    </div>
                )}

                {/* ===== Input Guards (3) ===== */}
                {fw !== "none" && fw !== "llama_guard" && inputGuards.length > 0 && (
                    <div className="settings-section">
                        <h3>Input Guards ({inputGuards.length})</h3>
                        {inputGuards.map((g) => (
                            <div className="setting-row" key={g.key}>
                                <span>{g.label}</span>
                                <Toggle checked={!!fwToggles[g.key]} onChange={() => toggleGuard(g.key)} />
                            </div>
                        ))}
                    </div>
                )}

                {/* ===== Output Guards (3) ===== */}
                {fw !== "none" && fw !== "llama_guard" && outputGuards.length > 0 && (
                    <div className="settings-section">
                        <h3>Output Guards ({outputGuards.length})</h3>
                        {outputGuards.map((g) => (
                            <div className="setting-row" key={g.key}>
                                <span>{g.label}</span>
                                <Toggle checked={!!fwToggles[g.key]} onChange={() => toggleGuard(g.key)} />
                            </div>
                        ))}
                    </div>
                )}

                {/* Llama Guard S1-S13 */}
                {fw === "llama_guard" && (
                    <div className="settings-section">
                        <h3>Categories (S1–S13)</h3>
                        {LLAMA_CATEGORIES.map(({ key, label }) => (
                            <div className="setting-row" key={key}>
                                <span><strong className="llama-key">{key}</strong> {label}</span>
                                <Toggle checked={!!fwToggles[key]} onChange={() => toggleGuard(key)} />
                            </div>
                        ))}
                    </div>
                )}

                {fw === "none" && (
                    <div className="settings-section settings-nudge">
                        <p>กรุณาเลือก Framework เพื่อเปิดใช้งาน Guardrails</p>
                    </div>
                )}
            </div>
        </div>
    );
}
