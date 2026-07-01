import React from 'react';
import { Settings, Shield, Key, Bell, Users } from 'lucide-react';

export default function SettingsPage() {
  return (
    <div className="p-8 max-w-4xl space-y-12">
      <div>
        <h1 className="text-3xl font-bold">Workspace Configuration</h1>
        <p className="text-slate-500">Manage enterprise defaults and security protocols.</p>
      </div>

      <div className="space-y-6">
        {[
          { icon: Key, label: 'Model Secrets', desc: 'Manage Ollama and DeepSeek API credentials.' },
          { icon: Shield, label: 'Security Gate', desc: 'Define automated failure thresholds for scoring.' },
          { icon: Users, label: 'Audit Access', desc: 'Configure which teams can view compliance reports.' },
        ].map((item, i) => (
          <div key={i} className="flex items-center justify-between p-6 bg-white border border-slate-200 rounded-3xl hover:shadow-lg transition-all cursor-pointer group">
            <div className="flex items-center space-x-6">
              <div className="w-12 h-12 bg-slate-100 rounded-2xl flex items-center justify-center text-slate-500 group-hover:bg-indigo-600 group-hover:text-white transition-colors">
                <item.icon className="w-6 h-6" />
              </div>
              <div>
                <h4 className="font-bold text-slate-900">{item.label}</h4>
                <p className="text-sm text-slate-500">{item.desc}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
