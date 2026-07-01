import React from 'react';
import { Award, Zap, Code, ShieldCheck } from 'lucide-react';

export const ScoreCard = ({ label, value, description, icon: Icon, color }: any) => {
  return (
    <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm flex flex-col space-y-4">
      <div className="flex items-center justify-between">
        <div className={`w-12 h-12 rounded-2xl flex items-center justify-center ${color} bg-opacity-10`}>
          <Icon className={`w-6 h-6 ${color.replace('bg-', 'text-')}`} />
        </div>
        <div className="text-2xl font-bold text-slate-900">{value}%</div>
      </div>
      <div>
        <h4 className="font-bold text-slate-800">{label}</h4>
        <p className="text-xs text-slate-500 mt-1">{description}</p>
      </div>
      <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
        <div className={`h-full ${color}`} style={{ width: `${value}%` }}></div>
      </div>
    </div>
  );
};
