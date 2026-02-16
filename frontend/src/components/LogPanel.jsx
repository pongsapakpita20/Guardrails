import React, { useEffect, useRef } from "react";

export default function LogPanel({ logs, onClear }) {
    const endRef = useRef(null);
    useEffect(() => endRef.current?.scrollIntoView({ behavior: "smooth" }), [logs]);

    return (
        <div className="panel log-panel">
            <div className="panel-header">
                <h2>
                    <span className="icon">⚡</span>
                    Live Logs
                </h2>
                <button className="clear-btn" onClick={onClear}>Clear</button>
            </div>

            <div className="panel-body">
                {logs.length === 0 && (
                    <div style={{ textAlign: "center", marginTop: "40%", color: "var(--text-dim)" }}>
                        <p style={{ fontSize: "0.85rem" }}>Waiting for activity...</p>
                    </div>
                )}

                {logs.map((l, i) => (
                    <div key={i} className={`log-entry ${l.status}`}>
                        <div className="log-header">
                            <span style={{ fontWeight: 600, color: "var(--primary)" }}>[{l.step}]</span>
                            <span>{new Date(l.timestamp).toLocaleTimeString()}</span>
                        </div>
                        <div className="log-content">{l.details}</div>
                        {l.latency > 0 && (
                            <div style={{ fontSize: "0.65rem", textAlign: "right", marginTop: "4px", opacity: 0.6 }}>
                                {l.latency.toFixed(3)}s
                            </div>
                        )}
                    </div>
                ))}
                <div ref={endRef} />
            </div>
        </div>
    );
}
