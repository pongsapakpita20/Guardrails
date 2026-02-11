import { useState, useRef, useEffect } from 'react';
import './App.css';

interface ConfigSwitches {
  violent_check: boolean;
  crime_check: boolean;
  sex_check: boolean;
  child_check: boolean;
  self_harm_check: boolean;
  hate_check: boolean;
  pii_check: boolean;
  off_topic_check: boolean;
}

interface ChatMessage {
  sender: string;
  text: string;
  status?: string;
  violation?: string; // เก็บประเภท violation แยกออกมาแสดงผลสวยๆ
}

function App() {
  const [input, setInput] = useState("");
  const [chatLog, setChatLog] = useState<ChatMessage[]>([]);
  const chatEndRef = useRef<HTMLDivElement>(null); // Auto scroll

  const [config, setConfig] = useState<ConfigSwitches>({
    violent_check: true,
    crime_check: true,
    sex_check: true,
    child_check: true,
    self_harm_check: true,
    hate_check: true,
    pii_check: false,
    off_topic_check: false,
  });

  // Auto scroll to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatLog]);

  const handleToggle = (key: keyof ConfigSwitches) => {
    setConfig(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const sendMessage = async () => {
    if (!input.trim()) return;

    const newLog = [...chatLog, { sender: "User", text: input, status: "user" }];
    setChatLog(newLog);
    const msgToSend = input;
    setInput(""); // Clear input early for better UX

    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msgToSend, config: config }),
      });
      
      const data = await res.json();
      
      setChatLog(prev => [...prev, { 
        sender: data.status === "blocked" ? "Guardrail" : "AI", 
        text: data.response,
        status: data.status, // 'success' or 'blocked'
        violation: data.violation
      }]);

    } catch (error) {
      console.error(error);
      setChatLog(prev => [...prev, { sender: "System", text: "Error connecting to server", status: "error" }]);
    }
  };

  return (
    <div className="app-container">
      
      {/* --- Left Panel: Control Switches --- */}
      <div className="panel control-panel">
        <div className="panel-header">
          <h2>🛡️ Guardrails Config</h2>
        </div>
        <div className="config-list">
          {Object.entries(config).map(([key, value]) => (
            <div 
              key={key} 
              className={`config-item ${value ? 'active' : 'inactive'}`}
              onClick={() => handleToggle(key as keyof ConfigSwitches)}
            >
              <span>{key.replace('_check', '').replace('_', ' ').toUpperCase()}</span>
              <input 
                type="checkbox" 
                checked={value} 
                readOnly // Managed by parent div click
              />
            </div>
          ))}
        </div>
      </div>

      {/* --- Right Panel: Chat Area --- */}
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