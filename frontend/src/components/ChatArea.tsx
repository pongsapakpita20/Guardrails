import React, { useEffect, useRef, useState } from 'react';
import type { ChatMessage, SystemStatus, Option } from '../types';
import './ChatArea.css';

interface ChatAreaProps {
    chatLog: ChatMessage[];
    input: string;
    setInput: (val: string) => void;
    sendMessage: () => void;
    isLoading: boolean;
    systemStatus: SystemStatus;
    
    // Props สำหรับ Dropdown ที่ย้ายมา
    frameworks: Option[];
    selectedFramework: string;
    setSelectedFramework: (val: string) => void;
    providers: Option[];
    selectedProvider: string;
    setSelectedProvider: (val: string) => void;
    models: string[];
    selectedModel: string;
    setSelectedModel: (val: string) => void;
    
    // Props สำหรับ Download Model
    onDownloadModel: (modelName: string) => void;
}

const ChatArea: React.FC<ChatAreaProps> = ({
    chatLog, input, setInput, sendMessage, isLoading, systemStatus,
    frameworks, selectedFramework, setSelectedFramework,
    providers, selectedProvider, setSelectedProvider,
    models, selectedModel, setSelectedModel,
    onDownloadModel
}) => {
    const chatEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);
    
    // State สำหรับ Modal ดาวน์โหลด
    const [showDownloadInput, setShowDownloadInput] = useState(false);
    const [newModelName, setNewModelName] = useState("");

    useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [chatLog, isLoading]);
    
    useEffect(() => {
        if (!isLoading && systemStatus === 'ready') {
            setTimeout(() => { inputRef.current?.focus(); }, 100);
        }
    }, [isLoading, systemStatus]);

    const handleDownloadSubmit = () => {
        if (newModelName.trim()) {
            onDownloadModel(newModelName);
            setNewModelName("");
            setShowDownloadInput(false);
        }
    };

    return (
        <div className="chat-container">
            {/* --- HEADER ใหม่: รวม Dropdown --- */}
            <div className="chat-header">
                <div className="header-left">
                    <div className="ai-icon">🤖</div>
                    <div style={{display:'flex', flexDirection:'column'}}>
                        <span style={{fontWeight:'bold', fontSize:'0.9rem'}}>AI Playground</span>
                        <div style={{display:'flex', alignItems:'center', gap:'5px'}}>
                            <span className={`status-dot ${systemStatus}`}></span>
                            <span style={{fontSize:'0.65rem', color:'#64748b'}}>{systemStatus.toUpperCase()}</span>
                        </div>
                    </div>
                </div>

                <div className="header-controls">
                    {/* 1. Framework */}
                    <select className="header-select" value={selectedFramework} onChange={(e) => setSelectedFramework(e.target.value)} title="Select Framework">
                        {frameworks.map(fw => <option key={fw.id} value={fw.id}>{fw.name}</option>)}
                    </select>

                    <span className="divider">|</span>

                    {/* 2. Provider */}
                    <select className="header-select" value={selectedProvider} onChange={(e) => setSelectedProvider(e.target.value)} title="Select Provider">
                        {providers.map(pv => <option key={pv.id} value={pv.id}>{pv.name}</option>)}
                    </select>

                    {/* 3. Model + Download Button */}
                    <div className="model-selector-group">
                        <select className="header-select model-select" value={selectedModel} onChange={(e) => setSelectedModel(e.target.value)} title="Select Model">
                            {models.length === 0 && <option value="">No models</option>}
                            {models.map(m => <option key={m} value={m}>{m}</option>)}
                        </select>
                        <button className="add-model-btn" onClick={() => setShowDownloadInput(!showDownloadInput)} title="Download New Model">
                            +
                        </button>
                    </div>
                </div>
            </div>

            {/* Input สำหรับ Download Model (แสดงเมื่อกด +) */}
            {showDownloadInput && (
                <div className="download-bar">
                    <input 
                        type="text" 
                        placeholder="Ex: llama3, qwen2.5:7b" 
                        value={newModelName}
                        onChange={(e) => setNewModelName(e.target.value)}
                    />
                    <button onClick={handleDownloadSubmit}>Download</button>
                    <button className="cancel" onClick={() => setShowDownloadInput(false)}>Cancel</button>
                </div>
            )}

            {/* ... (ส่วน Chat Window และ Input Area เหมือนเดิม) ... */}
            <div className="chat-window">
                {/* ... (Code เดิม) ... */}
                {chatLog.length === 0 && (
                    <div className="empty-state">
                        <div style={{fontSize: '3rem'}}>💬</div>
                        <p>Framework: {selectedFramework}</p>
                        <p style={{fontSize: '0.9rem', color: '#94a3b8'}}>{selectedProvider} / {selectedModel}</p>
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
                    ref={inputRef}
                    type="text" 
                    className="chat-input"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                    placeholder={systemStatus === 'ready' ? "พิมพ์ข้อความ..." : "Waiting for system..."}
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