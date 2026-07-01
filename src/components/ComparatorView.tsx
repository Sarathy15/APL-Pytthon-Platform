import React from 'react';
import { 
  CheckCircle2, 
  Zap, 
  Code2, 
  Fingerprint,
  Info,
  Maximize2,
  Terminal,
  MessageSquare
} from 'lucide-react';

const CodeSection = ({ title, code, language, icon: Icon, color, lineNumbers }: any) => {
  // Handle case where code might be an object instead of a string
  let codeString = typeof code === 'string' ? code : (code?.python_code || code?.code || JSON.stringify(code, null, 2) || '');
  
  return (
  <div className="flex flex-col h-full bg-slate-950 border border-slate-800 rounded-xl overflow-hidden shadow-2xl">
    <div className="p-3 bg-slate-900 border-b border-slate-800 flex items-center justify-between">
      <div className="flex items-center space-x-2">
        <Icon className={`w-4 h-4 ${color}`} />
        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{title}</span>
      </div>
      <div className="flex items-center space-x-2">
         <span className="text-[9px] font-mono text-slate-600 px-2 py-0.5 bg-slate-950 rounded border border-slate-800">{language}</span>
      </div>
    </div>
    <div className="flex-1 relative overflow-auto custom-scrollbar p-6">
       <div className="absolute left-0 top-0 bottom-0 w-10 bg-slate-900/30 border-r border-slate-800/50 flex flex-col items-center pt-6 space-y-4 text-[9px] font-mono text-slate-700 select-none">
          {codeString.split('\n').map((_: any, i: number) => <span key={i}>{String(i+1).padStart(2, '0')}</span>)}
       </div>
       <pre className="pl-10 font-mono text-xs leading-relaxed">
         {codeString.split('\n').map((line: string, i: number) => (
           <div key={i} className="group flex hover:bg-white/5 transition-colors">
              <code className={`${title.includes('Python') ? 'text-indigo-300' : 'text-amber-200'} whitespace-pre`}>
                {line}
              </code>
           </div>
         ))}
       </pre>
    </div>
  </div>
);};

export const ComparatorView = ({ apl, python, explanation }: { apl: string, python: string, explanation: any }) => {
  return (
    <div className="space-y-6 flex flex-col h-[calc(100vh-140px)]">
      <div className="flex items-center justify-between shrink-0">
        <div className="flex items-center space-x-4">
           <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center border border-emerald-100 shadow-sm">
             <Fingerprint className="w-6 h-6" />
           </div>
           <div>
             <h3 className="text-xl font-bold text-slate-900 tracking-tight">Semantic Transformation</h3>
             <p className="text-xs text-slate-500 font-medium">Equivalence: <span className="text-emerald-600 font-bold">{(explanation?.equivalence ?? explanation?.score) ?? 'Unavailable'}</span> | Proof Key: <span className="font-mono text-slate-400">{explanation?.proof_key ?? '—'}</span></p>
           </div>
        </div>
        <div className="flex items-center space-x-2">
           <button className="p-2 border border-slate-200 rounded-lg hover:bg-slate-50 text-slate-500 transition-colors">
             <Maximize2 className="w-4 h-4" />
           </button>
           <button className="bg-indigo-600 text-white px-6 py-2 rounded-lg font-bold text-xs uppercase tracking-widest hover:bg-indigo-700 shadow-lg shadow-indigo-600/20 transition-all active:scale-95">
             COMMIT TO REPO
           </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 flex-1 min-h-0">
        <CodeSection title="Legacy APL Source" code={apl} language="Dyalog APL" icon={Zap} color="text-amber-400" />
        <CodeSection title="Vectorized Python" code={python} language="Python 3.12 + NumPy" icon={Code2} color="text-indigo-400" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 shrink-0">
        <div className="lg:col-span-2 bg-white border border-slate-200 rounded-xl p-5 shadow-sm overflow-hidden relative">
           <div className="absolute right-0 top-0 p-4 opacity-5">
              <MessageSquare className="w-24 h-24" />
           </div>
           <div className="flex items-center space-x-2 mb-3 text-slate-400">
             <Info className="w-4 h-4" />
             <h4 className="text-[10px] font-bold uppercase tracking-widest">Inference Reasoning Trace</h4>
           </div>
           <div className="max-h-32 overflow-y-auto pr-2 custom-scrollbar">
              <p className="text-slate-600 leading-relaxed font-medium text-sm">
                {typeof explanation === 'string' ? explanation : (explanation?.summary || 'Logic mapping consistent across vector boundary.')}
              </p>
              {explanation?.lines && (
                 <div className="mt-4 space-y-2">
                    {explanation.lines.map((line: any, i: number) => (
                      <div key={i} className="flex items-start space-x-2 text-[11px] p-2 bg-slate-50 rounded border border-slate-100">
                         <span className="font-mono text-indigo-600 font-bold shrink-0">{line.code}</span>
                         <span className="text-slate-500">→ {line.explanation}</span>
                      </div>
                    ))}
                 </div>
              )}
           </div>
        </div>

        <div className="bg-slate-900 rounded-xl p-5 flex flex-col justify-between border border-slate-800 shadow-xl">
           <div className="flex items-center justify-between mb-4">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Metric Analysis</span>
              <Terminal className="w-3 h-3 text-slate-600" />
           </div>
           <div className="space-y-3">
              {[
                { label: 'Parity', value: explanation?.parity ?? 'Unavailable', color: 'text-emerald-400' },
                { label: 'Complexity', value: explanation?.complexity_change ?? 'Unavailable', color: 'text-sky-400' },
                { label: 'Vectorization', value: explanation?.vectorization ?? 'Unavailable', color: 'text-amber-400' },
              ].map((m, i) => (
                <div key={i} className="flex justify-between items-end border-b border-white/5 pb-2">
                   <span className="text-[10px] text-slate-500 font-medium uppercase tracking-tighter">{m.label}</span>
                   <span className={`text-xs font-bold font-mono ${m.color}`}>{m.value}</span>
                </div>
              ))}
           </div>
           <div className="mt-4 flex items-center justify-center space-x-2">
              <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]"></div>
              <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest">Validated Engine v2.1</span>
           </div>
        </div>
      </div>
    </div>
  );
};
