import React from 'react';
import { Navbar } from '../components/Navbar';
import { Activity, Shield, Terminal, ArrowRight } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white font-sans">
      <Navbar />
      
      <main className="max-w-7xl mx-auto px-8 py-20">
        <div className="text-center space-y-6 max-w-4xl mx-auto">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-slate-100 border text-xs font-bold text-slate-600 uppercase tracking-widest leading-none">
            <span className="w-2 h-2 rounded-full bg-indigo-500"></span>
            <span>Enterprise Pipeline V1.4 Ready</span>
          </div>
          <h1 className="text-6xl font-bold tracking-tighter text-slate-900">
            Automated APL <span className="text-indigo-600">$\rightarrow$</span> Python
            <br />Migration Platform
          </h1>
          <p className="text-xl text-slate-500 max-w-2xl mx-auto leading-relaxed">
            A secure, validation-driven platform for refactoring legacy finance and scientific systems using private local AI models.
          </p>
          
          <div className="pt-8 flex items-center justify-center space-x-4">
            <button className="bg-slate-900 text-white px-8 py-4 rounded-2xl font-bold text-lg hover:shadow-2xl hover:shadow-slate-200 transition-all">
              Initialize Migration
            </button>
            <button className="bg-white text-slate-900 border border-slate-200 px-8 py-4 rounded-2xl font-bold text-lg hover:bg-slate-50 transition-colors">
              Documentation
            </button>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-12 mt-32">
          <div className="space-y-4">
            <div className="w-12 h-12 bg-indigo-50 rounded-xl flex items-center justify-center text-indigo-600">
              <Shield className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-bold">Zero-Leakage Security</h3>
            <p className="text-slate-500 leading-relaxed">Local inference ensures that proprietary business logic never leaves your organizational boundaries.</p>
          </div>
          <div className="space-y-4">
            <div className="w-12 h-12 bg-emerald-50 rounded-xl flex items-center justify-center text-emerald-600">
              <Activity className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-bold">Behavioral Parity</h3>
            <p className="text-slate-500 leading-relaxed">Automated testcase generation compares APL and Python outputs with 1e-9 precision tolerance.</p>
          </div>
          <div className="space-y-4">
            <div className="w-12 h-12 bg-sky-50 rounded-xl flex items-center justify-center text-sky-600">
              <Terminal className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-bold">Agentic Refactoring</h3>
            <p className="text-slate-500 leading-relaxed">Specialized Qwen-Coder agents analyze semantics before generating modern NumPy implementations.</p>
          </div>
        </div>
      </main>
    </div>
  );
}
