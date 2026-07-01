import React from 'react';

export default function DashboardPage() {
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold">Migration Dashboard</h1>
      <p className="text-slate-500">Enterprise Asset View</p>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
        <div className="p-6 bg-white border rounded-2xl shadow-sm">
          <p className="text-sm font-medium text-slate-500">Active Jobs</p>
          <p className="text-2xl font-bold">24</p>
        </div>
        <div className="p-6 bg-white border rounded-2xl shadow-sm">
          <p className="text-sm font-medium text-slate-500">Success Rate</p>
          <p className="text-2xl font-bold text-emerald-600">92%</p>
        </div>
        <div className="p-6 bg-white border rounded-2xl shadow-sm">
          <p className="text-sm font-medium text-slate-500">System Load</p>
          <p className="text-2xl font-bold text-amber-600">Normal</p>
        </div>
      </div>
    </div>
  );
}
