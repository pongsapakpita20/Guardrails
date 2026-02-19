import React, { useEffect, useRef } from "react";

export default function LogPanel({ logs, onClear }) {
    const endRef = useRef(null);
    useEffect(() => endRef.current?.scrollIntoView({ behavior: "smooth" }), [logs]);

    return (
        <div className="panel log-panel">
            <div className="panel-header">
                <h2>
                    <span className="icon">▸</span>
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
                            <span>[{l.step}]</span>
                            <span>{new Date(l.timestamp).toLocaleTimeString()}</span>
                            {l.blocked && <span style={{ color: "var(--error)", marginLeft: "auto" }}>BLOCKED</span>}
                        </div>
                        <div className="log-content">{l.details}</div>
                        {(l.latency > 0 || (l.metrics && (l.metrics.cpu_percent != null || l.metrics.gpu_mem_mb != null))) && (
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
