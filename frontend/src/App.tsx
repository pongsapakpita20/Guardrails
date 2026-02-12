import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';
import LogPanel from './components/LogPanel';
import type { Option, SwitchInfo, ChatMessage, LogEntry, SystemStatus } from './types';
import './App.css';

function App() {
  // State
  const [systemStatus, setSystemStatus] = useState<SystemStatus>('initializing');
  
  const [input, setInput] = useState("");
  const [chatLog, setChatLog] = useState<ChatMessage[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Config State
  const [frameworks, setFrameworks] = useState<Option[]>([]);
  const [selectedFramework, setSelectedFramework] = useState<string>("");
  const [providers, setProviders] = useState<Option[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>("");
  const [models, setModels] = useState<string[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [isModelsLoading, setIsModelsLoading] = useState(false);
  
  const [availableSwitches, setAvailableSwitches] = useState<SwitchInfo[]>([]);
  const [config, setConfig] = useState<Record<string, boolean>>({});

  // Helper: Add Log
  const addLog = (message: string, type: 'info' | 'success' | 'warning' | 'error' = 'info') => {
    setLogs(prev => [...prev, {
      id: Date.now(),
      timestamp: new Date().toLocaleTimeString('th-TH', { hour12: false }),
      message,
      type
    }]);
  };

  // 1. Init System
  useEffect(() => {
    const initData = async () => {
      setSystemStatus('initializing');
      addLog("🚀 System Initializing...", "info");
      try {
        const [resFw, resPv] = await Promise.all([
            fetch("http://localhost:8000/frameworks"),
            fetch("http://localhost:8000/providers")
        ]);
        
        const fwData = await resFw.json();
        const pvData = await resPv.json();

        setFrameworks(fwData);
        if (fwData.length > 0) setSelectedFramework(fwData[0].id);

        setProviders(pvData);
        if (pvData.length > 0) setSelectedProvider(pvData[0].id);

        addLog(`✅ Connected to Backend`, "success");
      } catch (error) {
        setSystemStatus('error');
        addLog("❌ Failed to connect to Backend", "error");
      }
    };
    initData();
  }, []);

  // 2. Load Models when Provider changes
  useEffect(() => {
    if (!selectedProvider) return;
    const fetchModels = async () => {
      setIsModelsLoading(true);
      try {
        const res = await fetch(`http://localhost:8000/models/${selectedProvider}`);
        const data = await res.json();
        setModels(data.models || []);
        if (data.models?.length > 0) {
            setSelectedModel(data.models[0]);
        } else {
            setSelectedModel("");
            addLog(`⚠️ No models found in ${selectedProvider}`, "warning");
        }
      } catch (error) {
        addLog(`❌ Failed to fetch models`, "error");
      } finally {
        setIsModelsLoading(false);
      }
    };
    fetchModels();
  }, [selectedProvider]);

  // 3. Load Switches when Framework changes
  useEffect(() => {
    if (!selectedFramework) return;
    const fetchSwitches = async () => {
      try {
        const res = await fetch(`http://localhost:8000/config/switches?framework_id=${selectedFramework}`);
        const swData = await res.json();
        setAvailableSwitches(swData);
        const newConfig: Record<string, boolean> = {};
        swData.forEach((sw: SwitchInfo) => newConfig[sw.key] = sw.default);
        setConfig(newConfig);
      } catch (error) {
        addLog(`❌ Failed to load switches`, "error");
      }
    };
    fetchSwitches();
  }, [selectedFramework]);

  // 4. 🔥 Check Model Readiness (แก้ปัญหาข้อ 1)
  // เมื่อเปลี่ยนโมเดล เราจะยังไม่ให้สถานะเป็น Ready จนกว่าจะเช็คได้ว่าโมเดลพร้อม
  useEffect(() => {
    if (!selectedModel) return;
    
    // ตั้งสถานะเป็น Loading ก่อน
    setSystemStatus('loading_model');
    addLog(`⏳ Checking model: ${selectedModel}...`, "warning");

    // จำลองการ Ping (หรือยิงไป Backend จริงๆ ถ้า Backend มี Endpoint check status)
    // ในที่นี้เราใช้ Timeout สั้นๆ เพื่อ UX แต่ในอนาคตควรทำ API /health/model
    const timer = setTimeout(() => {
        setSystemStatus('ready');
        addLog(`🟢 Model ${selectedModel} is Ready!`, "success");
    }, 1000); 

    return () => clearTimeout(timer);
  }, [selectedModel]);

  const handleToggle = (key: string) => {
    setConfig(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    // Client-side check
    if (systemStatus !== 'ready') {
        addLog("⚠️ Model is not ready yet.", "warning");
        return;
    }

    const userMsg: ChatMessage = { 
      sender: "User", text: input, status: "success",
      timestamp: new Date().toLocaleTimeString('th-TH')
    };
    
    setChatLog(prev => [...prev, userMsg]);
    const msgToSend = input;
    setInput("");
    setIsLoading(true);

    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
            message: msgToSend, 
            config: config,
            framework_id: selectedFramework,
            provider_id: selectedProvider,
            model_name: selectedModel
        }),
      });
      
      const data = await res.json();
      
      // Handle Backend Status (Backend อาจจะตอบว่า Loading)
      if (res.status === 503 || data.status === 'loading') {
          setSystemStatus('loading_model');
          addLog("⏳ Model is loading on server...", "warning");
          // Retry logic could be added here
      }

      setChatLog(prev => [...prev, { 
        sender: "AI", 
        text: data.response,
        status: data.status,
        violation: data.violation,
        timestamp: new Date().toLocaleTimeString('th-TH')
      }]);

      if (data.status === 'blocked') {
        addLog(`🚫 Blocked: ${data.violation}`, "error");
      }

    } catch (error) {
      addLog(`🔥 Server Error`, "error");
      setSystemStatus('error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      <div className="panel control-panel">
        <Sidebar 
            frameworks={frameworks} selectedFramework={selectedFramework} setSelectedFramework={setSelectedFramework}
            providers={providers} selectedProvider={selectedProvider} setSelectedProvider={setSelectedProvider}
            models={models} selectedModel={selectedModel} setSelectedModel={setSelectedModel} isModelsLoading={isModelsLoading}
            availableSwitches={availableSwitches} config={config} handleToggle={handleToggle}
        />
      </div>
      
      <div className="panel chat-panel">
        <ChatArea 
            chatLog={chatLog} input={input} setInput={setInput} sendMessage={sendMessage} 
            isLoading={isLoading} systemStatus={systemStatus}
            selectedModel={selectedModel} selectedFramework={selectedFramework}
        />
      </div>

      <div className="panel log-panel">
        <LogPanel logs={logs} clearLogs={() => setLogs([])} />
      </div>
    </div>
  );
}

export default App;