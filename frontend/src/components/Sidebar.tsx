import React from 'react';
import type { Option, SwitchInfo } from '../types';
import './Sidebar.css';

interface SidebarProps {
    frameworks: Option[];
    selectedFramework: string;
    setSelectedFramework: (val: string) => void;
    
    providers: Option[];
    selectedProvider: string;
    setSelectedProvider: (val: string) => void;

    models: string[];
    selectedModel: string;
    setSelectedModel: (val: string) => void;
    isModelsLoading: boolean;

    availableSwitches: SwitchInfo[];
    config: Record<string, boolean>;
    handleToggle: (key: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({
    frameworks, selectedFramework, setSelectedFramework,
    providers, selectedProvider, setSelectedProvider,
    models, selectedModel, setSelectedModel, isModelsLoading,
    availableSwitches, config, handleToggle
}) => {
    return (
        <div className="sidebar-container">
            <div className="sidebar-header">
                <h2>⚙️ Configuration</h2>
            </div>

            <div className="sidebar-controls">
                <div className="control-group">
                    <label>🛡️ Framework</label>
                    <select value={selectedFramework} onChange={(e) => setSelectedFramework(e.target.value)}>
                        {frameworks.map(fw => <option key={fw.id} value={fw.id}>{fw.name}</option>)}
                    </select>
                </div>

                <div className="control-group">
                    <label>🔌 LLM Provider</label>
                    <select value={selectedProvider} onChange={(e) => setSelectedProvider(e.target.value)}>
                        {providers.map(pv => <option key={pv.id} value={pv.id}>{pv.name}</option>)}
                    </select>
                </div>

                <div className="control-group">
                    <label>🧠 Model {isModelsLoading && "⏳"}</label>
                    <select 
                        value={selectedModel} 
                        onChange={(e) => setSelectedModel(e.target.value)}
                        disabled={isModelsLoading || models.length === 0}
                    >
                        {models.length === 0 && <option>No models found</option>}
                        {models.map(m => <option key={m} value={m}>{m}</option>)}
                    </select>
                </div>
            </div>

            <div className="sidebar-switches">
                <div className="switches-label">ACTIVE RULES</div>
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