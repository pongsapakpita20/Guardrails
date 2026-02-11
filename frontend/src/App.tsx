import { useState, useRef, useEffect } from 'react';
import './App.css';

interface SwitchInfo {
  key: string;
  label: string;
  default: boolean;
  description?: string;
}

interface ChatMessage {
  sender: "User" | "AI" | "System";
  text: string;
  status?: "success" | "blocked" | "error";
  violation?: string;
  timestamp: string;
}

interface LogEntry {
  id: number;
  timestamp: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
}

function App() {
  const [input, setInput] = useState("");
  const [chatLog, setChatLog] = useState<ChatMessage[]>([]);
  const [availableSwitches, setAvailableSwitches] = useState<SwitchInfo[]>([]);
  const [config, setConfig] = useState<Record<string, boolean>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  
  const chatEndRef = useRef<HTMLDivElement>(null);
  const logsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatLog, isLoading]);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  useEffect(() => {
    const fetchConfig = async () => {
      addLog("System initializing...", "info");
      try {
        const res = await fetch("http://localhost:8000/config/switches");
        const switches: SwitchInfo[] = await res.json();
        setAvailableSwitches(switches);
        const initialConfig: Record<string, boolean> = {};
        switches.forEach(sw => initialConfig[sw.key] = sw.default);
        setConfig(initialConfig);
        addLog(`Loaded configuration: ${switches.length} rules found`, "success");
      } catch (error) {
        console.error("Failed to load switches:", error);
        addLog("Failed to connect to backend API", "error");
        setChatLog(prev => [...prev, { 
          sender: "System", 
          text: "⚠️ ไม่สามารถเชื่อมต่อกับ Backend ได้", 
          status: "error",
          timestamp: new Date().toLocaleTimeString()
        }]);
      }
    };
    fetchConfig();
  }, []);

  const addLog = (message: string, type: 'info' | 'success' | 'warning' | 'error' = 'info') => {
    setLogs(prev => [...prev, {
      id: Date.now(),
      timestamp: new Date().toLocaleTimeString([], { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" }),
      message,
      type
    }]);
  };

  const handleToggle = (key: string) => {
    const newValue = !config[key];
    setConfig(prev => ({ ...prev, [key]: newValue }));
    addLog(`Rule updated: ${key} is now ${newValue ? 'ON' : 'OFF'}`, "info");
  };

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMsg: ChatMessage = { 
      sender: "User", 
      text: input, 
      status: "success",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    
    setChatLog(prev => [...prev, userMsg]);
    const msgToSend = input;
    setInput("");
    setIsLoading(true);

    addLog(`📥 Received Input: "${msgToSend.substring(0, 20)}${msgToSend.length > 20 ? '...' : ''}"`, "info");
    addLog(`🛡️ Checking Input Guardrails...`, "warning");

    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msgToSend, config: config }),
      });
      
      const data = await res.json();
      
      if (data.status === 'blocked') {
        const isInputBlock = data.violation?.toLowerCase().includes('input') || data.violation?.toLowerCase().includes('jailbreak') || data.violation?.toLowerCase().includes('profanity');
        
        if (isInputBlock) {
             addLog(`🚫 Blocked at Input Stage: ${data.violation}`, "error");
        } else {
             addLog(`✅ Input Safe. Sending to LLM...`, "success");
             addLog(`🤖 LLM Generated Response`, "info");
             addLog(`🚫 Blocked at Output Stage: ${data.violation}`, "error");
        }
      } else {
        addLog(`✅ Input Safe. Sending to LLM...`, "success");
        addLog(`🤖 LLM Generated Response`, "info");
        addLog(`✅ Output Safe. Delivering to user.`, "success");
      }

      setChatLog(prev => [...prev, { 
        sender: "AI", 
        text: data.response,
        status: data.status,
        violation: data.violation,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);

    } catch (error) {
      addLog(`🔥 Network/Server Error`, "error");
      setChatLog(prev => [...prev, { 
        sender: "System", 
        text: "Error connecting to server", 
        status: "error",
        timestamp: new Date().toLocaleTimeString()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      
      {/* --- COLUMN 1: LEFT (Settings) --- */}
      <div className="panel control-panel">
        <div className="panel-header" style={{background: '#f8fafc', borderBottom: '1px solid #e2e8f0'}}>
          <h2 style={{fontSize: '1.1rem', color: '#334155'}}>⚙️ Controls</h2>
          <span style={{fontSize: '0.75rem', color: '#64748b'}}>
            {availableSwitches.length > 0 ? `${availableSwitches.length} Rules` : 'Loading...'}
          </span>
        </div>
        
        <div className="config-list">
          {availableSwitches.map((sw) => (
            <div 
              key={sw.key} 
              className={`config-item ${config[sw.key] ? 'active' : 'inactive'}`}
              onClick={() => handleToggle(sw.key)}
            >
              <div style={{display:'flex', flexDirection:'column'}}>
                <span style={{fontWeight: 600}}>{sw.label}</span>
              </div>
              <div className={`toggle-switch ${config[sw.key] ? 'on' : 'off'}`}></div>
            </div>
          ))}
        </div>
      </div>

      {/* --- COLUMN 2: CENTER (Chat) --- */}
      <div className="panel chat-panel">
        <div className="panel-header" style={{background: '#ffffff', borderBottom: '1px solid #f1f5f9', display:'flex', alignItems:'center', gap:'10px'}}>
          <div style={{width: 32, height: 32, background: '#2563eb', borderRadius: '50%', display:'flex', alignItems:'center', justifyContent:'center', color:'white'}}>🤖</div>
          <div>
            <h2 style={{fontSize: '1rem', margin:0}}>AI Guardrails Assistant</h2>
            <span style={{fontSize: '0.75rem', color: '#10b981'}}>● Online (Protected)</span>
          </div>
        </div>
        
        <div className="chat-window">
          {chatLog.length === 0 && (
            <div className="empty-state">
              <div style={{fontSize: '3rem'}}>💬</div>
              <p>สวัสดีครับ! ผมคือ AI ที่มีระบบความปลอดภัย</p>
              <p style={{fontSize: '0.9rem', color: '#94a3b8'}}>ลองพิมพ์อะไรบางอย่างเพื่อทดสอบ Guardrails ได้เลย</p>
            </div>
          )}
          
          {chatLog.map((msg, idx) => (
            <div key={idx} className={`message-row ${msg.sender === "User" ? "user" : "ai"}`}>
              {msg.sender === "AI" && <div className="avatar ai">🤖</div>}
              
              <div className={`message-bubble ${msg.sender === "User" ? "user-msg" : (msg.status === "blocked" ? "blocked-msg" : "ai-msg")}`}>
                {msg.status === "blocked" && (
                  <div className="violation-badge">🛡️ BLOCKED: {msg.violation}</div>
                )}
                <div style={{whiteSpace: 'pre-wrap'}}>{msg.text}</div>
                <div className="timestamp">{msg.timestamp}</div>
              </div>

              {msg.sender === "User" && <div className="avatar user">👤</div>}
            </div>
          ))}

          {isLoading && (
            <div className="message-row ai">
              <div className="avatar ai">🤖</div>
              <div className="message-bubble ai-msg loading">
                <span className="dot">.</span><span className="dot">.</span><span className="dot">.</span>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>
        
        <div className="input-area">
          <input 
            type="text" 
            className="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="พิมพ์ข้อความของคุณ..."
            disabled={isLoading}
          />
          <button className="send-btn" onClick={sendMessage} disabled={isLoading}>
            {isLoading ? '...' : 'Send'}
          </button>
        </div>
      </div>

      {/* --- COLUMN 3: RIGHT (Logs) --- */}
      <div className="panel log-panel" style={{ background: '#0f172a', color: '#38bdf8', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '15px', background: '#1e293b', borderBottom: '1px solid #334155', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.9rem', fontWeight: 'bold', fontFamily: 'monospace' }}> {'>'}_ System Logs</span>
            <button onClick={() => setLogs([])} style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '0.7rem' }}>CLEAR</button>
        </div>
        <div style={{ flex: 1, overflowY: 'auto', padding: '10px', fontFamily: 'monospace', fontSize: '0.8rem', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {logs.length === 0 && <span style={{color: '#475569', fontStyle: 'italic', textAlign: 'center', marginTop: '20px'}}>-- No Activity --</span>}
            {logs.map((log) => (
                <div key={log.id} style={{ display: 'flex', gap: '8px', lineHeight: '1.4' }}>
                    <span style={{ color: '#64748b', minWidth: '60px', fontSize: '0.75rem' }}>[{log.timestamp}]</span>
                    <span style={{ 
                        color: log.type === 'error' ? '#ef4444' : 
                               log.type === 'success' ? '#4ade80' : 
                               log.type === 'warning' ? '#facc15' : '#e2e8f0',
                        wordBreak: 'break-word'
                    }}>
                        {log.type === 'info' ? 'ℹ️' : log.type === 'success' ? '✅' : log.type === 'warning' ? '⚡' : '❌'} {log.message}
                    </span>
                </div>
            ))}
            <div ref={logsEndRef} />
        </div>
      </div>

    </div>
  );
}

export default App;