import React from 'react';
import type { SwitchInfo } from '../types';
import './Sidebar.css';

interface SidebarProps {
    availableSwitches: SwitchInfo[];
    config: Record<string, boolean>;
    handleToggle: (key: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ availableSwitches, config, handleToggle }) => {
    return (
        <div className="sidebar-container">
            <div className="sidebar-header">
                <h2>⚙️ Guardrails Rules</h2>
            </div>
            {/* เอาส่วน Dropdown ออกไปแล้ว */}
            <div className="sidebar-switches">
                {availableSwitches.map((sw) => (
                    <div key={sw.key} className={`config-item ${config[sw.key] ? 'active' : 'inactive'}`} onClick={() => handleToggle(sw.key)}>
                        <span>{sw.label}</span>
                        <div className={`toggle-switch ${config[sw.key] ? 'on' : 'off'}`}></div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default Sidebar;