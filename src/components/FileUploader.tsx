import React, { useState } from 'react';
import { Upload, X, FileCode, CheckCircle2, AlertCircle, Cpu, Command, ArrowRight, ShieldCheck, Zap } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

export const FileUploader = ({ onUpload }: { onUpload: (code: string) => void }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [code, setCode] = useState('');

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(e.type === 'dragover');
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  return (
    <div className="max-w-6xl mx-auto space-y-12">
      <div className="flex items-end justify-between">
        <div>
          <div className="flex items-center space-x-2 text-indigo-600 mb-2">
            <Cpu className="w-5 h-5" />
            <span className="text-[10px] font-bold uppercase tracking-[0.2em]">Data Ingestion Node</span>
          </div>
          <h2 className="text-4xl font-bold text-slate-900 tracking-tight">Mainframe Migration Port</h2>
        </div>
        <div className="flex space-x-8 text-right">
           <div>
             <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Queue Status</p>
             <p className="text-sm font-bold text-emerald-500">READY</p>
           </div>
           <div>
             <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Encrypted Tunnel</p>
             <p className="text-sm font-bold text-slate-700 font-mono">TLS 1.3 ENABLED</p>
           </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-1 overflow-hidden border border-slate-200 rounded-2xl shadow-xl">
        <div
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          className={`h-[500px] flex flex-col items-center justify-center space-y-6 transition-all duration-500 bg-white group ${
            isDragging ? 'bg-indigo-50/50' : ''
          }`}
        >
          <div className="relative">
             <div className="absolute inset-0 bg-indigo-500/10 blur-2xl rounded-full scale-150 animate-pulse"></div>
             <div className="w-24 h-24 bg-white border border-slate-100 rounded-3xl shadow-xl flex items-center justify-center text-indigo-600 relative z-10 group-hover:scale-110 transition-transform">
               <Upload className="w-10 h-10" />
             </div>
          </div>
          <div className="text-center px-12">
            <p className="text-slate-800 font-bold text-xl">Sequential Asset Upload</p>
            <p className="text-sm text-slate-500 mt-2 leading-relaxed">Drop APL source files (.apl, .dyalog) into the secure buffer for batch processing.</p>
          </div>
          <div className="flex space-x-4">
             <button className="bg-slate-900 text-white px-8 py-3 rounded-xl font-bold text-sm shadow-xl shadow-slate-900/10 hover:bg-slate-800 transition-all flex items-center space-x-2">
               <span>BROWSE SOURCE</span>
               <ArrowRight className="w-4 h-4" />
             </button>
          </div>
        </div>

        <div className="h-[500px] flex flex-col bg-slate-950 border-l border-slate-200">
           <div className="p-4 bg-slate-900 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center space-x-3">
                 <Command className="w-4 h-4 text-slate-500" />
                 <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Manual Ingestion Buffer</span>
              </div>
              <button 
                onClick={() => onUpload(code)}
                disabled={!code}
                className="group flex items-center space-x-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 text-white px-4 py-1.5 rounded-lg text-xs font-bold transition-all"
              >
                <span>INITIATE MIGRATION</span>
                <Cpu className="w-3.5 h-3.5" />
              </button>
           </div>
           <div className="flex-1 relative group">
              <div className="absolute left-0 top-0 bottom-0 w-12 bg-slate-900/50 border-r border-slate-800 flex flex-col items-center pt-6 space-y-4 text-[10px] font-mono text-slate-600 select-none">
                 <span>01</span>
                 <span>02</span>
                 <span>03</span>
                 <span>04</span>
              </div>
              <textarea
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="⍝ Enter APL expressions directly for rapid prototyping...&#10;x ← ⍳10&#10;+/x"
                className="w-full h-full bg-transparent pl-16 p-6 font-mono text-indigo-100 text-sm focus:outline-none resize-none placeholder:text-slate-700 leading-relaxed"
              ></textarea>
           </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
         {[
           { icon: ShieldCheck, label: 'Secure Buffer', desc: 'Auto-scrubs PII and sensitive mainframe traces before inference.' },
           { icon: Zap, label: 'LVM Optimized', desc: 'Leverages Large Vector Models for high-fidelity code mapping.' },
           { icon: AlertCircle, label: 'Traceable Logic', desc: 'Every line generates a semantic proof for compliance audits.' },
         ].map((feat, i) => (
           <div key={i} className="flex items-start space-x-4">
              <div className="w-10 h-10 bg-white border border-slate-100 rounded-xl flex items-center justify-center text-slate-400 shrink-0 shadow-sm">
                 <feat.icon className="w-5 h-5" />
              </div>
              <div>
                 <h4 className="font-bold text-slate-800 text-sm">{feat.label}</h4>
                 <p className="text-xs text-slate-500 mt-1 leading-relaxed">{feat.desc}</p>
              </div>
           </div>
         ))}
      </div>
    </div>
  );
};
