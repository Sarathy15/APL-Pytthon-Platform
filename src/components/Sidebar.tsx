import React from 'react';
import { 
  BarChart3, 
  Settings, 
  ShieldCheck, 
  Zap, 
  LayoutGrid, 
  Terminal, 
  Database, 
  Cpu,
  History,
  Box
} from 'lucide-react';

const navItems = [
  { icon: LayoutGrid, label: 'Control Center', id: 'dashboard' },
  { icon: Cpu, label: 'Ingestion Hub', id: 'upload' },
  { icon: History, label: 'Migration Trace', id: 'reports' },
  { icon: ShieldCheck, label: 'Validator', id: 'validation' },
  { icon: BarChart3, label: 'Analytics', id: 'scores' },
  { icon: Settings, label: 'Cluster Config', id: 'settings' },
];

export const Sidebar = ({ activeTab, onTabChange }: { activeTab: string, onTabChange: (id: string) => void }) => {
  return (
    <div className="w-64 h-full bg-slate-950 text-slate-400 flex flex-col border-r border-slate-800">
      <div className="p-8 pb-4">
        <div className="flex items-center space-x-3 mb-8">
          <div className="w-8 h-8 rounded-md bg-indigo-600 flex items-center justify-center">
            <Box className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-slate-100 tracking-tight">APL MIGRATOR</h1>
            <p className="text-[10px] text-slate-500 font-mono tracking-widest uppercase">System v2.4.1</p>
          </div>
        </div>
      </div>

      <div className="px-4 space-y-1 flex-1 overflow-y-auto">
        <p className="px-4 text-[10px] font-bold text-slate-600 uppercase tracking-widest mb-2">Main Pipeline</p>
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onTabChange(item.id)}
            className={`w-full flex items-center justify-between px-4 py-2.5 rounded-lg transition-all group ${
              activeTab === item.id 
              ? 'bg-slate-800 text-slate-100 shadow-sm border border-slate-700' 
              : 'hover:bg-slate-900 hover:text-slate-200'
            }`}
          >
            <div className="flex items-center space-x-3">
              <item.icon className={`w-4 h-4 ${activeTab === item.id ? 'text-indigo-400' : 'text-slate-500'}`} />
              <span className="text-sm font-medium">{item.label}</span>
            </div>
          </button>
        ))}
      </div>

      <div className="p-4 bg-slate-900/50 m-4 rounded-xl border border-slate-800">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]"></div>
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Local Inference</span>
          </div>
          <span className="text-[10px] font-mono text-slate-600">Ollama/Qwen</span>
        </div>
        <div className="h-1 bg-slate-800 rounded-full overflow-hidden">
          <div className="w-2/3 h-full bg-indigo-500 rounded-full"></div>
        </div>
        <div className="flex justify-between mt-2 text-[10px] font-mono text-slate-500">
          <span>GPU Load 64%</span>
          <span>RAM 82%</span>
        </div>
      </div>

      <div className="p-6 border-t border-slate-800 flex items-center space-x-3">
        <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-[10px] font-bold text-slate-400">
          AD
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-bold text-slate-200 truncate">Sarathy P.</p>
          <p className="text-[10px] text-slate-500 truncate">sarathypachaiyappan@gmail.com</p>
        </div>
      </div>
    </div>
  );
};
