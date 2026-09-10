import React from 'react';
import { Database, ShieldCheck, Activity } from 'lucide-react';

interface HeaderProps {
  activeTab: string;
  apiConnected?: boolean;
  dbConnected?: boolean;
  trgmEnabled?: boolean;
}

const TAB_TITLES: Record<string, string> = {
  dashboard: 'Executive Dashboard & BSR Overview',
  import: 'Import Center – Document Analysis Pipeline',
  search: 'Rate Search & Explorer',
  compare: 'Cross-Provincial Rate Comparison Matrix',
  review: 'Data Verification & Review Queue',
  sources: 'Source File Archive & Traceability',
  master: 'Canonical Master Item Mapping Registry',
  settings: 'System Configuration & LAN Management',
};

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  apiConnected = true,
  dbConnected = true,
  trgmEnabled = true,
}) => {
  return (
    <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between shadow-xs">
      <div>
        <h1 className="text-lg font-bold text-slate-900 tracking-tight">
          {TAB_TITLES[activeTab] || 'BSR Rate Hub'}
        </h1>
        <p className="text-xs text-slate-500">
          Sri Lanka National & Provincial Building Schedule of Rates
        </p>
      </div>

      <div className="flex items-center gap-3">
        {/* PostgreSQL Status */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-100 rounded-full text-xs text-slate-700 border border-slate-200">
          <Database className={`w-3.5 h-3.5 ${dbConnected ? 'text-emerald-600' : 'text-rose-500'}`} />
          <span className="font-medium">{dbConnected ? 'PostgreSQL 16' : 'DB Disconnected'}</span>
        </div>

        {/* Trigram Extension Status */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-100 rounded-full text-xs text-slate-700 border border-slate-200">
          <ShieldCheck className={`w-3.5 h-3.5 ${trgmEnabled ? 'text-blue-600' : 'text-amber-500'}`} />
          <span className="font-medium">{trgmEnabled ? 'pg_trgm Active' : 'Trigram Off'}</span>
        </div>

        {/* Live API Pulse */}
        <div className="flex items-center gap-1.5 text-xs pl-2">
          <Activity className={`w-3.5 h-3.5 ${apiConnected ? 'text-emerald-500 animate-pulse' : 'text-rose-500'}`} />
          <span className={`font-medium hidden sm:inline ${apiConnected ? 'text-slate-600' : 'text-rose-600'}`}>
            {apiConnected ? 'Online' : 'API Offline'}
          </span>
        </div>
      </div>
    </header>
  );
};
