import React from 'react';
import Link from 'next/link';

export const Navbar = () => {
  return (
    <nav className="h-16 border-b flex items-center justify-between px-8 bg-white">
      <div className="flex items-center space-x-2">
        <div className="w-8 h-8 bg-indigo-600 rounded"></div>
        <span className="font-bold text-xl">APL Migrator</span>
      </div>
      <div className="flex space-x-6 text-sm font-medium">
        <Link href="/dashboard" className="text-slate-600 hover:text-indigo-600">Dashboard</Link>
        <Link href="/upload" className="text-slate-600 hover:text-indigo-600">Upload</Link>
        <Link href="/reports" className="text-slate-600 hover:text-indigo-600">Reports</Link>
      </div>
    </nav>
  );
}
