import React, { useEffect, useRef, useState } from "react";

/* Map violation type → icon + label + color class */
const VIOLATION_INFO = {
    PII: { icon: "🔒", label: "PII Detected", cls: "guard-pii" },
    Jailbreak: { icon: "🛡️", label: "Jailbreak Blocked", cls: "guard-jailbreak" },
    "Off-Topic": { icon: "🚫", label: "Off-Topic", cls: "guard-offtopic" },
    Toxicity: { icon: "⚠️", label: "Toxicity Detected", cls: "guard-toxicity" },
    Hallucination: { icon: "🔍", label: "Hallucination", cls: "guard-hallucination" },
    Competitor: { icon: "🏢", label: "Competitor Mention", cls: "guard-competitor" },
    "Llama Guard": { icon: "🦙", label: "Llama Guard", cls: "guard-llama" },
    NeMoUnavailable: { icon: "⚙️", label: "NeMo Unavailable", cls: "guard-error" },
    NeMoError: { icon: "⚙️", label: "NeMo Error", cls: "guard-error" },
    "Server Error": { icon: "💥", label: "Server Error", cls: "guard-error" },
};

function getViolationInfo(type) {
    return VIOLATION_INFO[type] || { icon: "⛔", label: type || "Blocked", cls: "guard-default" };
}

/* Clean [RAIL:XXX] prefixes from displayed text */
function cleanContent(text) {
    return text?.replace(/\[RAIL:\w+\]\s*/g, "").replace(/\[SAFE\]\s*/g, "").trim() || "";
}

export default function ChatPanel({ messages, onSend, loading }) {
    const [text, setText] = useState("");
    const endRef = useRef(null);

    useEffect(() => endRef.current?.scrollIntoView({ behavior: "smooth" }), [messages, loading]);

    const submit = () => {
        if (!text.trim() || loading) return;
        onSend(text.trim());
        setText("");
    };

    return (
        <div className="panel chat-panel">
            <div className="panel-header">
                <h2>
                    <span className="icon">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
                    </span>
                    Guardrails AI
                </h2>
            </div>

            <div className="panel-body">
                {messages.length === 0 && (
                    <div className="chat-empty">
                        <div className="chat-empty-icon">AI</div>
                        <h3>Guardrails AI Chat</h3>
                        <p>Ask a question. The Guardrails engine will intercept.</p>
                    </div>
                )}

                <div className="chat-messages">
                    {messages.map((m, i) => {
                        const info = m.blocked ? getViolationInfo(m.violation) : null;
                        const displayContent = cleanContent(m.content);

                        return (
                            <div key={i} className={`message ${m.role} ${m.blocked ? `blocked ${info.cls}` : ""}`}>
                                {/* Blocked message — enhanced UI */}
                                {m.blocked && (
                                    <div className="guard-card">
                                        <div className="guard-header">
                                            <span className="guard-icon">{info.icon}</span>
                                            <span className="guard-label">{info.label}</span>
                                            {m.framework && (
                                                <span className="guard-framework">{m.framework}</span>
                                            )}
                                        </div>
                                        <div className="guard-body">
                                            {displayContent}
                                        </div>
                                        <div className="guard-shimmer"></div>
                                    </div>
                                )}

                                {/* Normal bot response */}
                                {!m.blocked && m.role === "bot" && (
                                    <>
                                        {m.framework && (
                                            <span className="framework-pill">
                                                ✓ {m.framework}
                                            </span>
                                        )}
                                        <div>{displayContent}</div>
                                    </>
                                )}

                                {/* User message */}
                                {m.role === "user" && (
                                    <div>{m.content}</div>
                                )}
                            </div>
                        );
                    })}

                    {loading && (
                        <div className="typing">
                            <span></span><span></span><span></span>
                        </div>
                    )}
                    <div ref={endRef} />
                </div>
            </div>

            <div className="chat-input-bar">
                <div className="chat-input-wrapper">
                    <input
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && submit()}
                        placeholder="สอบถามข้อมูลรถไฟ..."
                        disabled={loading}
                    />
                    <button onClick={submit} disabled={loading || !text.trim()}>
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
                    </button>
                </div>
            </div>
        </div>
    );
}
