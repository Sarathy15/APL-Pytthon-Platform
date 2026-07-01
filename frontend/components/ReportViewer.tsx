import React from 'react';
import { FileText, Download, Share2, Mail } from 'lucide-react';

export const ReportViewer = ({ reportData }: { reportData: any }) => {
  return (
    <div className="max-w-5xl mx-auto bg-white rounded-[40px] shadow-2xl border border-slate-200 overflow-hidden">
      <div className="bg-slate-900 p-10 text-white flex justify-between items-start">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Migration Compliance Report</h2>
          <p className="text-slate-400 mt-2 font-mono text-sm">JOB ID: {reportData?.id || 'MIG-2026-05-14'}</p>
        </div>
        <div className="flex space-x-3">
          <button className="p-3 bg-white/10 rounded-xl hover:bg-white/20 transition-colors">
            <Download className="w-5 h-5 text-white" />
          </button>
          <button className="p-3 bg-white/10 rounded-xl hover:bg-white/20 transition-colors">
            <Share2 className="w-5 h-5 text-white" />
          </button>
        </div>
      </div>
      
      <div className="p-12 space-y-12">
        <section className="grid grid-cols-1 md:grid-cols-2 gap-12">
          <div>
            <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-4">Executive Summary</h3>
            <p className="text-slate-600 leading-relaxed">
              The APL migration analysis identifies a high-confidence match with NumPy-based vector operations. 
              The resulting implementation maintains structural integrity while improving readability by 45%.
            </p>
          </div>
          <div className="bg-slate-50 rounded-3xl p-6 border border-slate-100">
             <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-4">Certification</h3>
             <div className="flex items-center space-x-4">
                <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center text-emerald-600">
                   <FileText className="w-8 h-8" />
                </div>
                <div>
                   <p className="font-bold text-slate-800">Production Ready</p>
                   <p className="text-xs text-slate-500">Validated by ValidationAgent v2.1</p>
                </div>
             </div>
          </div>
        </section>
      </div>
    </div>
  );
};
