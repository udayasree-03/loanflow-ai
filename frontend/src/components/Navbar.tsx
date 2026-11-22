import React from 'react';
import { ShieldCheck, Sparkles, Activity } from 'lucide-react';

interface NavbarProps {
  onHomeClick: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onHomeClick }) => {
  return (
    <header className="sticky top-0 z-30 bg-slate-900 border-b border-slate-800 text-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div
          onClick={onHomeClick}
          className="flex items-center space-x-3 cursor-pointer group select-none"
        >
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/20 group-hover:scale-105 transition-transform">
            <ShieldCheck className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-1.5">
              <span className="font-bold text-lg tracking-tight text-white">LoanFlow</span>
              <span className="text-xs px-1.5 py-0.5 rounded font-semibold bg-blue-500/20 text-blue-300 border border-blue-400/30">
                AI
              </span>
            </div>
            <p className="text-xs text-slate-400">Intelligent Mortgage Underwriting</p>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 text-xs bg-slate-800/80 px-3 py-1.5 rounded-full border border-slate-700">
            <Activity className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
            <span className="text-slate-300">LangGraph Agent: <span className="text-emerald-400 font-medium">Ready</span></span>
          </div>
          <div className="hidden sm:flex items-center space-x-1 text-xs text-slate-400">
            <Sparkles className="w-3.5 h-3.5 text-blue-400" />
            <span>Fannie Mae 43% DTI Conforming Rules</span>
          </div>
        </div>
      </div>
    </header>
  );
};
