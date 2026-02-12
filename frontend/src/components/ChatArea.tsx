import React, { useEffect, useRef } from 'react';
import type { ChatMessage, SystemStatus } from '../types';
import './ChatArea.css';

interface ChatAreaProps {
    chatLog: ChatMessage[];
    input: string;
    setInput: (val: string) => void;
    sendMessage: () => void;
    isLoading: boolean;
    systemStatus: SystemStatus;
    selectedModel: string;
    selectedFramework: string;
}

const ChatArea: React.FC<ChatAreaProps> = ({
    chatLog, input, setInput, sendMessage, isLoading, systemStatus, selectedModel, selectedFramework
}) => {
    const chatEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null); // 1. สร้าง Ref

    // Auto Scroll
    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [chatLog, isLoading]);

    // 2. Fix: Auto Focus เมื่อโหลดเสร็จ
    useEffect(() => {
        if (!isLoading && systemStatus === 'ready') {
            // หน่วงเวลานิดนึงเพื่อให้ UI Render เสร็จ
            setTimeout(() => {
                inputRef.current?.focus();
            }, 100);
        }
    }, [isLoading, systemStatus]);

    return (
        <div className="chat-container">
            <div className="chat-header">
                <div className="ai-icon">🤖</div>
                <div>
                    <h2 style={{margin:0, fontSize: '1rem'}}>AI Guardrails Assistant</h2>
                    <span className={`status-dot ${systemStatus}`}></span>
                    <span style={{fontSize: '0.75rem', color: '#64748b'}}>
                         {systemStatus === 'ready' ? `Online | ${selectedFramework} | ${selectedModel}` : systemStatus.toUpperCase()}
                    </span>
                </div>
            </div>

            <div className="chat-window">
                {chatLog.length === 0 && (
                    <div className="empty-state">
                        <div style={{fontSize: '3rem'}}>💬</div>
                        <p>พร้อมเริ่มงานครับ</p>
                    </div>
                )}
                
                {chatLog.map((msg, idx) => (
                    <div key={idx} className={`message-row ${msg.sender === "User" ? "user" : "ai"}`}>
                        {msg.sender === "AI" && <div className="avatar ai">🤖</div>}
                        <div className={`message-bubble ${msg.sender === "User" ? "user-msg" : (msg.status === "blocked" ? "blocked-msg" : "ai-msg")}`}>
                            {msg.status === "blocked" && <div className="violation-badge">🛡️ BLOCKED: {msg.violation}</div>}
                            <div style={{whiteSpace: 'pre-wrap'}}>{msg.text}</div>
                            <div className="timestamp">{msg.timestamp}</div>
                        </div>
                        {msg.sender === "User" && <div className="avatar user">👤</div>}
                    </div>
                ))}
                
                {isLoading && (
                    <div className="message-row ai">
                        <div className="avatar ai">🤖</div>
                        <div className="message-bubble ai-msg loading">Thinking...</div>
                    </div>
                )}
                <div ref={chatEndRef} />
            </div>

            <div className="input-area">
                <input 
                    ref={inputRef} // 3. ผูก Ref
                    type="text" 
                    className="chat-input"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                    placeholder={systemStatus === 'ready' ? "พิมพ์ข้อความ..." : "กำลังโหลดโมเดล..."}
                    disabled={isLoading || systemStatus !== 'ready'}
                />
                <button className="send-btn" onClick={sendMessage} disabled={isLoading || systemStatus !== 'ready'}>
                    Send
                </button>
            </div>
        </div>
    );
};

export default ChatArea;