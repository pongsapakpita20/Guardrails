const API_URL = "http://localhost:8000";
const WS_URL = "ws://localhost:8000/ws/logs";

// -------- REST --------
export async function fetchModels(backend = "ollama") {
    try {
        const res = await fetch(`${API_URL}/models?backend=${backend}`);
        const data = await res.json();
        return data.models ?? [];
    } catch {
        return [];
    }
}

export async function fetchHealth(backend = "ollama") {
    try {
        const res = await fetch(`${API_URL}/health?backend=${backend}`);
        return await res.json();
    } catch {
        return null;
    }
}

export async function sendChat(payload) {
    const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`Server error ${res.status}`);
    return await res.json();
}

// -------- WebSocket --------
export function connectLogs(onLog) {
    let ws;
    function open() {
        ws = new WebSocket(WS_URL);
        ws.onmessage = (e) => onLog(JSON.parse(e.data));
        ws.onclose = () => setTimeout(open, 2000);
        ws.onerror = () => ws.close();
    }
    open();
    return () => ws?.close();
}
