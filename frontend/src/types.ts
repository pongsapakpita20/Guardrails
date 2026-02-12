// frontend/src/types.ts
export interface Option {
    id: string;
    name: string;
}
  
export interface SwitchInfo {
    key: string;
    label: string;
    default: boolean;
    description?: string;
}
  
export interface ChatMessage {
    sender: "User" | "AI" | "System";
    text: string;
    status?: "success" | "blocked" | "error";
    violation?: string;
    timestamp: string;
}
  
export interface LogEntry {
    id: number;
    timestamp: string;
    message: string;
    type: 'info' | 'success' | 'warning' | 'error';
}

// เพิ่ม Type สำหรับสถานะระบบ
export type SystemStatus = 'initializing' | 'ready' | 'loading_model' | 'error';