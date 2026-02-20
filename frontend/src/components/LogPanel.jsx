import React, { useEffect, useRef } from "react";

export default function LogPanel({ logs, onClear }) {
    const endRef = useRef(null);
    useEffect(() => endRef.current?.scrollIntoView({ behavior: "smooth" }), [logs]);

    return (
        <div className="panel log-panel">
            <div className="panel-header">
                <h2>
                    <span className="icon">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="4 17 10 11 4 5"></polyline><line x1="12" y1="19" x2="20" y2="19"></line></svg>
                    </span>
                    Live Logs
                </h2>
                <button className="clear-btn" onClick={onClear}>Clear</button>
            </div>

            <div className="panel-body">
                {logs.length === 0 && (
                    <div className="log-empty">
                        <p>Waiting for activity...</p>
                    </div>
                )}

                {logs.map((l, i) => (
                    <div key={i} className={`log-entry ${l.status} ${l.blocked ? "blocked" : ""}`}>
                        <div className="log-header">
                            <span className="step-badge">[{l.step}]</span>
                            <span className="timestamp">{new Date(l.timestamp).toLocaleTimeString()}</span>
                            {l.blocked && <span style={{ color: "var(--error)", marginLeft: "auto", fontWeight: "bold" }}>BLOCKED</span>}
                        </div>
                        {/* Use pre-wrap to preserve newlines from backend formatting */}
                        <div className="log-content" style={{ whiteSpace: "pre-wrap", fontFamily: "monospace" }}>{l.details}</div>

                        {/* Only show metrics row if details is NOT multiline (to avoid duplication) */}
                        {(!l.details || !l.details.includes("\n")) && (l.latency > 0 || (l.metrics && (l.metrics.cpu_percent != null || l.metrics.gpu_mem_mb != null))) && (
                            <div className="metrics-row">
                                {l.latency > 0 && <span>{l.latency.toFixed(2)}s</span>}
                                {l.metrics?.cpu_percent != null && <span>CPU {l.metrics.cpu_percent}%</span>}
                                {l.metrics?.gpu_mem_mb != null && <span>GPU {l.metrics.gpu_mem_mb} MB</span>}
                            </div>
                        )}
                    </div>
                ))}
                <div ref={endRef} />
            </div>
        </div>
    );
}
