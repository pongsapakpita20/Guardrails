import React, { useEffect, useRef, useState } from "react";

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
                    <span className="icon">◆</span>
                    SRT Call Center
                </h2>
            </div>

            <div className="panel-body">
                {messages.length === 0 && (
                    <div className="chat-empty">
                        <div className="chat-empty-icon">SRT</div>
                        <h3>น้องรางรถไฟ</h3>
                        <p>ผู้ช่วยอัจฉริยะแห่งการรถไฟแห่งประเทศไทย</p>
                    </div>
                )}

                <div className="chat-messages">
                    {messages.map((m, i) => (
                        <div key={i} className={`message ${m.role} ${m.blocked ? "blocked" : ""}`}>
                            {m.blocked && (
                                <div className="violation-badge">{m.violation || "Blocked"}</div>
                            )}
                            {m.framework && !m.blocked && (
                                <span className="framework-badge" style={{
                                    fontSize: "0.65rem", padding: "2px 6px", borderRadius: "4px",
                                    marginBottom: "4px", display: "inline-block", opacity: 0.8
                                }}>
                                    {m.framework}
                                </span>
                            )}
                            <div>{m.content}</div>
                        </div>
                    ))}

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
