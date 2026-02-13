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
    
    frameworks: Option[];
    selectedFramework: string;
    setSelectedFramework: (val: string) => void;
    providers: Option[];
    selectedProvider: string;
    setSelectedProvider: (val: string) => void;
    models: string[];
    selectedModel: string;
    setSelectedModel: (val: string) => void;
    
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
    
    const [showDownloadInput, setShowDownloadInput] = useState(false);
    const [newModelName, setNewModelName] = useState("");

    useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [chatLog, isLoading]);
    
    useEffect(() => {
        if (!isLoading && systemStatus === 'ready') {
            setTimeout(() => { inputRef.current?.focus(); }, 100);
        }
    }, [isLoading, systemStatus]);

    // ✅ Logic ใหม่สำหรับปุ่ม +
    const handleAddModelClick = () => {
        if (selectedProvider === 'gpustack') {
            // ถ้าเป็น GPUStack ให้เปิดหน้า Dashboard
            window.open('http://localhost:10101', '_blank');
        } else {
            // ถ้าเป็น Ollama ให้โชว์ช่องโหลด
            setShowDownloadInput(!showDownloadInput);
        }
    };

    const handleDownloadSubmit = () => {
        if (newModelName.trim()) {
            onDownloadModel(newModelName);
            setNewModelName("");
            setShowDownloadInput(false);
        }
    };

    return (
        <div className="chat-container">
            <div className="chat-header">
                <div className="header-left">
                    <div className="ai-icon">🤖</div>
                    <div style={{display:'flex', flexDirection:'column'}}>
                        <span style={{fontWeight:'bold', fontSize:'0.9rem'}}>AI Playground</span>
                        <div style={{display:'flex', alignItems:'center', gap:'5px'}}>
                            <span className={`status-dot ${systemStatus}`}></span>
                            <span style={{fontSize:'0.65rem', color:'#64748b'}}>
                                {/* ✅ แสดงข้อความ Loading ชัดๆ */}
                                {systemStatus === 'loading_model' ? 'LOADING MODEL...' : systemStatus.toUpperCase()}
                            </span>
                        </div>
                    </div>
                </div>

                <div className="header-controls">
                    <select className="header-select" value={selectedFramework} onChange={(e) => setSelectedFramework(e.target.value)}>
                        {frameworks.map(fw => <option key={fw.id} value={fw.id}>{fw.name}</option>)}
                    </select>

                    <span className="divider">|</span>

                    <select className="header-select" value={selectedProvider} onChange={(e) => setSelectedProvider(e.target.value)}>
                        {providers.map(pv => <option key={pv.id} value={pv.id}>{pv.name}</option>)}
                    </select>

                    <div className="model-selector-group">
                        <select 
                            className="header-select model-select" 
                            value={selectedModel} 
                            onChange={(e) => setSelectedModel(e.target.value)}
                            disabled={systemStatus === 'loading_model'} // ล็อกตอนโหลด
                        >
                            {models.length === 0 && <option value="">No models</option>}
                            {models.map(m => <option key={m} value={m}>{m}</option>)}
                        </select>
                        
                        {/* ✅ ปุ่ม + ที่เปลี่ยน Logic แล้ว */}
                        <button 
                            className="add-model-btn" 
                            onClick={handleAddModelClick}
                            title={selectedProvider === 'gpustack' ? "Open GPUStack Dashboard" : "Download New Model"}
                        >
                            +
                        </button>
                    </div>
                </div>
            </div>

            {/* ✅ Overlay ตอนโหลดโมเดล (Optional: จะได้เห็นชัดๆ) */}
            {systemStatus === 'loading_model' && (
                <div className="model-loading-overlay">
                    <div className="spinner"></div>
                    <p>⏳ Loading Model: {selectedModel}...</p>
                    <small>Please wait, this might take a few seconds.</small>
                </div>
            )}

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

            <div className="chat-window">
                {/* ... (Code เดิม) ... */}
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