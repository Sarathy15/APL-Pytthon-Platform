import React from 'react';

export default function ReportsPage() {
  return (
    <div className="p-8 space-y-6">
      <h1 className="text-3xl font-bold">Audit History</h1>
      <div className="bg-white border rounded-3xl overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-slate-50 border-b">
            <tr>
              <th className="p-4 text-xs font-bold text-slate-400 uppercase">Job ID</th>
              <th className="p-4 text-xs font-bold text-slate-400 uppercase">Status</th>
              <th className="p-4 text-xs font-bold text-slate-400 uppercase">Parity</th>
              <th className="p-4 text-xs font-bold text-slate-400 uppercase">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {[1, 2, 3].map(i => (
              <tr key={i} className="hover:bg-slate-50 transition-colors">
                <td className="p-4 font-mono text-sm">MIG-2026-05-{i}</td>
                <td className="p-4"><span className="px-2 py-1 bg-emerald-100 text-emerald-700 text-xs font-bold rounded">Certified</span></td>
                <td className="p-4 text-sm font-semibold">100%</td>
                <td className="p-4"><button className="text-indigo-600 font-bold text-xs">View PDF</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
