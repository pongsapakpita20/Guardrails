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

function App() {
  const [input, setInput] = useState("");
  const [chatLog, setChatLog] = useState<ChatMessage[]>([]);
  const [availableSwitches, setAvailableSwitches] = useState<SwitchInfo[]>([]);
  const [config, setConfig] = useState<Record<string, boolean>>({});
  const [isLoading, setIsLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Auto scroll
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatLog, isLoading]);

  // Load Config
  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const res = await fetch("http://localhost:8000/config/switches");
        const switches: SwitchInfo[] = await res.json();
        setAvailableSwitches(switches);
        const initialConfig: Record<string, boolean> = {};
        switches.forEach(sw => initialConfig[sw.key] = sw.default);
        setConfig(initialConfig);
      } catch (error) {
        console.error("Failed to load switches:", error);
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

  const handleToggle = (key: string) => {
    setConfig(prev => ({ ...prev, [key]: !prev[key] }));
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
    setIsLoading(true); // เริ่มโหลด

    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msgToSend, config: config }),
      });
      
      const data = await res.json();
      
      setChatLog(prev => [...prev, { 
        sender: "AI", 
        text: data.response,
        status: data.status,
        violation: data.violation,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);

    } catch (error) {
      setChatLog(prev => [...prev, { 
        sender: "System", 
        text: "Error connecting to server", 
        status: "error",
        timestamp: new Date().toLocaleTimeString()
      }]);
    } finally {
      setIsLoading(false); // โหลดเสร็จ
    }
  };

  return (
    <div className="app-container">
      
      {/* --- Sidebar (Settings) --- */}
      <div className="panel control-panel">
        <div className="panel-header" style={{background: '#f8fafc', borderBottom: '1px solid #e2e8f0'}}>
          <h2 style={{fontSize: '1.1rem', color: '#334155'}}>⚙️ Security Controls</h2>
          <span style={{fontSize: '0.75rem', color: '#64748b'}}>
            {availableSwitches.length > 0 ? `${availableSwitches.length} Active Rules` : 'Initializing...'}
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
                {/* <span style={{fontSize: '0.7rem', opacity: 0.7}}>{sw.description || sw.key}</span> */}
              </div>
              <div className={`toggle-switch ${config[sw.key] ? 'on' : 'off'}`}></div>
            </div>
          ))}
        </div>
      </div>

      {/* --- Main Chat Area --- */}
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
    </div>
  );
}

export default App;