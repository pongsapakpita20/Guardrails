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
                    <span className="icon">◇</span>
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
