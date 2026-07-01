import React, { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { 
  Activity, 
  ShieldCheck, 
  Zap, 
  Database, 
  Server, 
  Terminal,
  ArrowUpRight,
  ArrowDownRight,
  RefreshCw,
  MoreVertical
} from 'lucide-react';
import { BASE_URL } from '../lib/gemini';

const data: any[] = [];

const TechnicalStat = ({ label, value, trend, unit }: any) => (
  <div className="bg-white border-r border-b border-slate-200 p-6 flex flex-col justify-between hover:bg-slate-50 transition-colors">
    <div>
       <div className="flex items-center justify-between mb-1">
         <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{label}</span>
         <MoreVertical className="w-3 h-3 text-slate-300 cursor-pointer" />
       </div>
       <div className="flex items-baseline space-x-1">
         <span className="text-2xl font-bold text-slate-900 tabular-nums">{value ?? '—'}</span>
         <span className="text-xs font-medium text-slate-400">{unit}</span>
       </div>
    </div>
    <div className={`flex items-center space-x-1 text-[10px] font-bold mt-4 ${trend > 0 ? 'text-emerald-500' : 'text-rose-500'}`}>
       {trend > 0 ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
       <span>{Math.abs(trend)}% vs prev cycle</span>
    </div>
  </div>
);

export const Dashboard = () => {
  const [backendHealth, setBackendHealth] = React.useState<{status:string,version?:string} | null>(null);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const res = await fetch(`${BASE_URL}/api/health`);
        if (!mounted) return;
        if (res.ok) setBackendHealth(await res.json());
        else setBackendHealth({ status: 'unavailable' });
      } catch (e) {
        if (!mounted) return;
        setBackendHealth({ status: 'down' });
      }
    })();
    return () => { mounted = false };
  }, []);
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">Control Center</h2>
          <div className="flex items-center space-x-4 mt-1">
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${backendHealth && backendHealth.status === 'healthy' ? 'bg-emerald-500' : 'bg-rose-500'}`}></div>
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Backend: {backendHealth?.status ?? 'unknown'}</span>
            </div>
            <div className="w-1 h-1 rounded-full bg-slate-300"></div>
            <span className="text-xs font-medium text-slate-400">Version: {backendHealth?.version ?? '—'}</span>
          </div>
        </div>
        <div className="flex items-center space-x-2">
           <button className="flex items-center space-x-2 p-2 px-3 bg-white border border-slate-200 rounded-lg text-xs font-bold text-slate-600 hover:bg-slate-50 transition-all">
             <RefreshCw className="w-3.5 h-3.5" />
             <span>RELOAD REPO</span>
           </button>
           <button className="flex items-center space-x-2 p-2 px-4 bg-indigo-600 rounded-lg text-xs font-bold text-white hover:bg-indigo-700 transition-all shadow-sm">
             <span>DEPLOY AGENT</span>
           </button>
        </div>
      </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 rounded-xl border-l border-t border-slate-200 overflow-hidden shadow-sm">
        <TechnicalStat label="Backend Status" value={backendHealth?.status ?? '—'} trend={0} unit="" />
        <TechnicalStat label="Backend Version" value={backendHealth?.version ?? '—'} trend={0} unit="" />
        <TechnicalStat label="Migration Throughput" value={null} trend={0} unit="OPS" />
        <TechnicalStat label="Validation Accuracy" value={null} trend={0} unit="%" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm p-6">
           <div className="flex items-center justify-between mb-8">
             <div className="flex items-center space-x-3">
               <div className="w-8 h-8 rounded-lg bg-indigo-50 flex items-center justify-center text-indigo-600">
                 <Activity className="w-4 h-4" />
               </div>
               <h4 className="font-bold text-slate-800 text-sm">System Utilization</h4>
             </div>
             <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 rounded-full bg-indigo-500"></div>
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Load Factor</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 rounded-full bg-slate-200"></div>
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Baseline</span>
                </div>
             </div>
           </div>
           <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data}>
                  <defs>
                    <linearGradient id="colorLoad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366f1" stopOpacity={0.1}/>
                      <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#94a3b8', fontSize: 10, fontFamily: 'JetBrains Mono'}} dy={10} />
                  <YAxis axisLine={false} tickLine={false} tick={{fill: '#94a3b8', fontSize: 10, fontFamily: 'JetBrains Mono'}} />
                  <Tooltip 
                    contentStyle={{borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)', fontFamily: 'JetBrains Mono'}}
                    labelStyle={{display: 'none'}}
                  />
                  <Area type="monotone" dataKey="load" stroke="#6366f1" strokeWidth={2} fillOpacity={1} fill="url(#colorLoad)" />
                </AreaChart>
              </ResponsiveContainer>
           </div>
        </div>

        <div className="bg-slate-900 rounded-xl border border-slate-800 shadow-sm p-6 text-slate-300">
           <div className="flex items-center space-x-3 mb-6">
             <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center text-slate-400 border border-white/10">
               <Terminal className="w-4 h-4" />
             </div>
             <h4 className="font-bold text-sm text-white">Live Pipeline Trace</h4>
           </div>
           
           <div className="space-y-4 h-[280px] overflow-y-auto pr-2 custom-scrollbar">
             <div className="text-[12px] text-slate-500">Live trace not available. Backend must provide trace API to populate this view.</div>
           </div>

           <button className="w-full mt-6 py-2 rounded-lg bg-white/5 border border-white/10 text-[10px] font-bold uppercase tracking-widest hover:bg-white/10 transition-all text-slate-400">
             Open Security Vault
           </button>
        </div>
      </div>
    </div>
  );
};
