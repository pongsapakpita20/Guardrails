import { useState, useRef, useEffect } from 'react';
import './App.css';

// 1. นิยามโครงสร้างข้อมูลที่รับจาก API
interface SwitchInfo {
  key: string;
  label: string;
  default: boolean;
  description?: string;
}

interface ChatMessage {
  sender: string;
  text: string;
  status?: string;
  violation?: string;
}

function App() {
  const [input, setInput] = useState("");
  const [chatLog, setChatLog] = useState<ChatMessage[]>([]);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // 2. State ใหม่: เก็บรายชื่อสวิตช์ที่ Server มี
  const [availableSwitches, setAvailableSwitches] = useState<SwitchInfo[]>([]);
  
  // 3. State เดิม: เก็บค่าเปิด/ปิด (แต่ตอนนี้เป็น Dynamic Object)
  const [config, setConfig] = useState<Record<string, boolean>>({});

  // Auto scroll
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatLog]);

  // 4. Load Config เมื่อเปิดหน้าเว็บ
  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const res = await fetch("http://localhost:8000/config/switches");
        const switches: SwitchInfo[] = await res.json();
        
        // เก็บรายชื่อสวิตช์ไว้สร้างปุ่ม
        setAvailableSwitches(switches);

        // ตั้งค่า Default (เปิด/ปิด) ตามที่ Server บอกมา
        const initialConfig: Record<string, boolean> = {};
        switches.forEach(sw => {
          initialConfig[sw.key] = sw.default;
        });
        setConfig(initialConfig);

      } catch (error) {
        console.error("Failed to load switches:", error);
        // Fallback กรณีต่อ Server ไม่ติด
        setChatLog(prev => [...prev, { sender: "System", text: "⚠️ ไม่สามารถเชื่อมต่อกับ Backend ได้ กรุณาเช็ค Docker", status: "error" }]);
      }
    };

    fetchConfig();
  }, []);

  const handleToggle = (key: string) => {
    setConfig(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const sendMessage = async () => {
    if (!input.trim()) return;

    const newLog = [...chatLog, { sender: "User", text: input, status: "user" }];
    setChatLog(newLog);
    const msgToSend = input;
    setInput("");

    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        // ส่ง Config ปัจจุบันไปให้ Backend
        body: JSON.stringify({ message: msgToSend, config: config }),
      });
      
      const data = await res.json();
      
      setChatLog(prev => [...prev, { 
        sender: data.status === "blocked" ? "Guardrail" : "AI", 
        text: data.response,
        status: data.status,
        violation: data.violation
      }]);

    } catch (error) {
      console.error(error);
      setChatLog(prev => [...prev, { sender: "System", text: "Error connecting to server", status: "error" }]);
    }
  };

  return (
    <div className="app-container">
      
      {/* --- Left Panel: Dynamic Control Switches --- */}
      <div className="panel control-panel">
        <div className="panel-header">
          <h2>🛡️ Active Guardrails</h2>
          {/* แสดงชื่อ Engine ที่ใช้อยู่ (ดูจากจำนวนปุ่มเอาก็ได้) */}
          <span style={{fontSize: '0.8rem', color: '#666'}}>
            {availableSwitches.length > 0 ? `Loaded ${availableSwitches.length} Rules` : 'Loading...'}
          </span>
        </div>
        
        <div className="config-list">
          {availableSwitches.length === 0 && (
            <div style={{padding: '20px', textAlign: 'center', color: '#999'}}>
              ⏳ Connecting to Guard Engine...
            </div>
          )}

          {availableSwitches.map((sw) => (
            <div 
              key={sw.key} 
              className={`config-item ${config[sw.key] ? 'active' : 'inactive'}`}
              onClick={() => handleToggle(sw.key)}
              title={sw.description}
            >
              <span>{sw.label}</span>
              <input 
                type="checkbox" 
                checked={config[sw.key] || false} 
                readOnly 
              />
            </div>
          ))}
        </div>
      </div>

      {/* --- Right Panel: Chat Area (เหมือนเดิม) --- */}
      <div className="panel chat-panel">
        <div className="panel-header">
          <h2>💬 Chat Testing Playground</h2>
        </div>
        
        <div className="chat-window">
          {chatLog.length === 0 && (
            <div style={{textAlign: 'center', color: '#9ca3af', marginTop: '50px'}}>
              เริ่มการสนทนาเพื่อทดสอบ Guardrails...
            </div>
          )}
          
          {chatLog.map((msg, idx) => (
            <div key={idx} className={`message-row ${msg.sender === "User" ? "user" : "ai"}`}>
              <div className={`message-bubble ${msg.sender === "User" ? "user-msg" : (msg.status === "blocked" ? "blocked-msg" : "ai-msg")}`}>
                {msg.status === "blocked" && (
                  <div className="violation-tag">🚫 {msg.violation}</div>
                )}
                <div>{msg.text}</div>
              </div>
            </div>
          ))}
          <div ref={chatEndRef} />
        </div>
        
        <div className="input-area">
          <input 
            type="text" 
            className="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Type a message to test..."
          />
          <button className="send-btn" onClick={sendMessage}>Send</button>
        </div>
      </div>
    </div>
  );
}

export default App;