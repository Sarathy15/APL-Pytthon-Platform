import React from 'react';
import { Loader2 } from 'lucide-react';

export const Loader = ({ message }: { message?: string }) => {
  return (
    <div className="flex flex-col items-center justify-center p-12 space-y-4">
      <Loader2 className="w-10 h-10 text-indigo-600 animate-spin" />
      <p className="text-slate-500 font-medium animate-pulse">{message || 'Processing Migration Cycle...'}</p>
    </div>
  );
};
