import { useState, useEffect, useCallback } from 'react'; // เพิ่ม useCallback
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';
import LogPanel from './components/LogPanel';
import type { Option, SwitchInfo, ChatMessage, LogEntry, SystemStatus } from './types';
import './App.css';

function App() {
  // --- State ---
  const [systemStatus, setSystemStatus] = useState<SystemStatus>('initializing');
  const [isBackendConnected, setIsBackendConnected] = useState(false); // เช็คว่าต่อ Backend ติดไหม
  
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

  const addLog = (message: string, type: 'info' | 'success' | 'warning' | 'error' = 'info') => {
    setLogs(prev => [...prev, {
      id: Date.now(),
      timestamp: new Date().toLocaleTimeString('th-TH', { hour12: false }),
      message,
      type
    }]);
  };

  // --- 🔥 1. ระบบ Auto-Retry Connection (หัวใจสำคัญ) ---
  const fetchSystemData = useCallback(async () => {
    try {
      // 1. ลองยิง Health Check ก่อน
      const healthRes = await fetch("http://localhost:8000/health");
      if (!healthRes.ok) throw new Error("Backend not ready");

      // 2. ถ้า Backend ตื่นแล้ว ค่อยดึงข้อมูลจริง
      const [resFw, resPv] = await Promise.all([
          fetch("http://localhost:8000/frameworks"),
          fetch("http://localhost:8000/providers")
      ]);
      
      const fwData = await resFw.json();
      const pvData = await resPv.json();

      setFrameworks(fwData);
      if (!selectedFramework && fwData.length > 0) setSelectedFramework(fwData[0].id);

      setProviders(pvData);
      if (!selectedProvider && pvData.length > 0) setSelectedProvider(pvData[0].id);

      setIsBackendConnected(true); // ✅ เชื่อมต่อสำเร็จ
      addLog("✅ Connected to Backend System", "success");
      
      return true; // บอกว่าทำสำเร็จแล้ว

    } catch (error) {
      // ถ้าพัง (Backend ยังไม่ตื่น)
      console.warn("Retrying connection...");
      setIsBackendConnected(false);
      return false; // บอกว่ายังไม่สำเร็จ
    }
  }, [selectedFramework, selectedProvider]); // Dependencies

  // --- 🔥 2. useEffect วนลูปเช็คจนกว่าจะติด ---
  useEffect(() => {
    let intervalId: any;

    const initLoop = async () => {
      // ลองดึงข้อมูล
      const success = await fetchSystemData();
      
      if (success) {
        // ถ้าสำเร็จแล้ว ให้หยุดวนลูป (หรือจะวนเช็ค Health ต่อก็ได้ แต่นี่เอาแค่โหลดข้อมูลครั้งแรกพอ)
        setSystemStatus('ready');
      } else {
        // ถ้ายังไม่สำเร็จ ให้ตั้งสถานะเป็น Error ไว้ก่อน แล้วรอ Interval รอบหน้า
        setSystemStatus('error');
      }
    };

    // รันครั้งแรกทันที
    initLoop();

    // ตั้งเวลาให้ลองใหม่ทุกๆ 3 วินาที ถ้ายังเชื่อมไม่ได้
    if (!isBackendConnected) {
        intervalId = setInterval(initLoop, 3000);
    }

    return () => {
        if (intervalId) clearInterval(intervalId);
    };
  }, [isBackendConnected, fetchSystemData]);


  // --- 3. Load Models (เมื่อ Provider เปลี่ยน) ---
  useEffect(() => {
    if (!selectedProvider || !isBackendConnected) return; // ถ้า Backend หลุด ไม่ต้องทำ
    
    const fetchModels = async () => {
      setIsModelsLoading(true);
      try {
        const res = await fetch(`http://localhost:8000/models/${selectedProvider}`);
        const data = await res.json();
        setModels(data.models || []);
        
        // Logic เลือกโมเดล: ถ้าตัวเดิมยังมีอยู่ก็ใช้ตัวเดิม ถ้าไม่มีให้ใช้ตัวแรก
        if (data.models?.length > 0) {
            if (!data.models.includes(selectedModel)) {
                setSelectedModel(data.models[0]);
            }
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
  }, [selectedProvider, isBackendConnected]); // เพิ่ม isBackendConnected เป็น Trigger

  // --- 4. Load Switches (เมื่อ Framework เปลี่ยน) ---
  useEffect(() => {
    if (!selectedFramework || !isBackendConnected) return;

    const fetchSwitches = async () => {
      try {
        const res = await fetch(`http://localhost:8000/config/switches?framework_id=${selectedFramework}`);
        const swData = await res.json();
        setAvailableSwitches(swData);
        
        // Preserve existing config if possible, else reset
        const newConfig: Record<string, boolean> = {};
        swData.forEach((sw: SwitchInfo) => {
             // ถ้าเคยตั้งค่าไว้แล้วให้ใช้ค่าเดิม ถ้าไม่เคยให้ใช้ค่า default
             newConfig[sw.key] = config[sw.key] !== undefined ? config[sw.key] : sw.default;
        });
        setConfig(newConfig);
      } catch (error) {
        addLog(`❌ Failed to load switches`, "error");
      }
    };
    fetchSwitches();
  }, [selectedFramework, isBackendConnected]);

  // --- 5. Status Checker Logic ---
  useEffect(() => {
     if (!isBackendConnected) {
         setSystemStatus('error');
         return;
     }
     if (isModelsLoading) {
         setSystemStatus('loading_model');
         return;
     }
     setSystemStatus('ready');
  }, [isBackendConnected, isModelsLoading]);


  const handleToggle = (key: string) => {
    setConfig(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    if (systemStatus !== 'ready') {
        addLog("⚠️ System is not ready. Please wait...", "warning");
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
      addLog(`🔥 Connection Lost`, "error");
      setIsBackendConnected(false); // ตัด Connection ทันทีเพื่อให้ Auto-Retry ทำงาน
    } finally {
      setIsLoading(false);
    }
  };
  const handleDownloadModel = async (modelName: string) => {
    addLog(`⬇️ Requesting download for: ${modelName}...`, "info");
    try {
        const res = await fetch("http://localhost:8000/model/pull", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                provider_id: selectedProvider,
                model_name: modelName
            })
        });
        const data = await res.json();
        if (data.status === 'started') {
            addLog(`✅ Download started! Please watch the LOGS panel.`, "success");
            addLog(`ℹ️ Note: This may take several minutes.`, "info");
        } else {
            addLog(`⚠️ ${data.message}`, "warning");
        }
    } catch (error) {
        addLog(`❌ Failed to trigger download`, "error");
    }
  };
  return (
    <div className="app-container">
      {/* แสดง Overlay ถ้า Backend ยังเชื่อมไม่ได้ 
          เพื่อให้รู้ว่าระบบกำลังพยายามเชื่อมต่ออยู่ 
      */}
      {!isBackendConnected && (
          <div style={{
              position: 'fixed', top: 0, left: 0, width: '100%', height: '5px', 
              background: '#ef4444', zIndex: 9999, 
              animation: 'pulse 1s infinite'
          }} title="Trying to connect to backend..." />
      )}

      <div className="panel control-panel">
        <Sidebar 
            // Sidebar รับของน้อยลงแล้ว เหลือแค่ Switch
            availableSwitches={availableSwitches} config={config} handleToggle={handleToggle}
        />
      </div>
      
      <div className="panel chat-panel">
        <ChatArea 
            chatLog={chatLog} input={input} setInput={setInput} sendMessage={sendMessage} 
            isLoading={isLoading} systemStatus={systemStatus}
            
            // ส่ง Dropdown ไปให้ ChatArea แทน
            frameworks={frameworks} selectedFramework={selectedFramework} setSelectedFramework={setSelectedFramework}
            providers={providers} selectedProvider={selectedProvider} setSelectedProvider={setSelectedProvider}
            models={models} selectedModel={selectedModel} setSelectedModel={setSelectedModel}
            
            // ส่งฟังก์ชันโหลดโมเดล
            onDownloadModel={handleDownloadModel}
        />
      </div>

      <div className="panel log-panel">
        <LogPanel logs={logs} clearLogs={() => setLogs([])} />
      </div>
    </div>
  );
}

export default App;