import React, { useEffect, useRef } from 'react';
import type { LogEntry } from '../types';
import './LogPanel.css';

const LogPanel: React.FC<{ logs: LogEntry[], clearLogs: () => void }> = ({ logs, clearLogs }) => {
    const logsEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [logs]);

    return (
        <div className="log-panel">
            <div className="log-header">
                <span>{'>'}_ System Logs</span>
                <button onClick={clearLogs}>CLEAR</button>
            </div>
            <div className="log-content">
                {logs.length === 0 && <div className="no-logs">-- No Activity --</div>}
                {logs.map((log) => (
                    <div key={log.id} className="log-entry">
                        <span className="log-time">[{log.timestamp}]</span>
                        <span className={`log-msg ${log.type}`}>
                            {log.type === 'info' ? 'ℹ️' : log.type === 'success' ? '✅' : log.type === 'warning' ? '⚡' : '❌'} {log.message}
                        </span>
                    </div>
                ))}
                <div ref={logsEndRef} />
            </div>
        </div>
    );
};

export default LogPanel;