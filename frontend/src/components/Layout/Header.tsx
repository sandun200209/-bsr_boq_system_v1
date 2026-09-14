import React from 'react';
import { Database, ShieldCheck, Activity, Menu, User as UserIcon, LogOut } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface HeaderProps {
  activeTab: string;
  apiConnected?: boolean;
  dbConnected?: boolean;
  trgmEnabled?: boolean;
  onOpenSidebar?: () => void;
}

const TAB_TITLES: Record<string, string> = {
  dashboard: 'Executive Dashboard & BSR Overview',
  import: 'Import Center – Document Pipeline',
  search: 'Rate Search & Explorer',
  compare: 'Cross-Provincial Rate Matrix',
  review: 'Verification & Review Queue',
  sources: 'Source Archive & Cloud Storage',
  master: 'Canonical Master Item Registry',
  users: 'User Management & Audit Trail',
  settings: 'System Configuration & LAN',
};

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  apiConnected = true,
  dbConnected = true,
  trgmEnabled = true,
  onOpenSidebar,
}) => {
  const { user, logout } = useAuth();

  const getRoleBadgeStyle = (role?: string) => {
    switch (role) {
      case 'ADMIN':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      case 'MANAGER':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'USER':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'VIEWER':
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-3 sm:px-6 flex items-center justify-between shadow-xs sticky top-0 z-30">
      {/* Left: Mobile Hamburger & Title */}
      <div className="flex items-center gap-2.5 sm:gap-3 min-w-0">
        <button
          type="button"
          onClick={onOpenSidebar}
          className="lg:hidden p-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-xl transition-colors shrink-0"
          aria-label="Open menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="min-w-0">
          <h1 className="text-sm sm:text-base font-bold text-slate-900 tracking-tight truncate">
            {TAB_TITLES[activeTab] || 'BSR Rate Hub'}
          </h1>
          <p className="text-[11px] text-slate-500 hidden sm:block truncate">
            Sri Lanka Multi-Sector Schedule of Rates & Centralized Cloud Storage
          </p>
        </div>
      </div>

      {/* Right: Status Pills & User Profile */}
      <div className="flex items-center gap-2 sm:gap-3 shrink-0">
        {/* Database Status (Hidden on very small screens) */}
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 bg-slate-100 rounded-full text-xs text-slate-700 border border-slate-200">
          <Database className={`w-3.5 h-3.5 ${dbConnected ? 'text-emerald-600' : 'text-rose-500'}`} />
          <span className="font-medium">{dbConnected ? 'Cloud PostgreSQL' : 'DB Disconnected'}</span>
        </div>

        {/* Trigram Extension Status (Hidden on mobile/tablet) */}
        <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 bg-slate-100 rounded-full text-xs text-slate-700 border border-slate-200">
          <ShieldCheck className={`w-3.5 h-3.5 ${trgmEnabled ? 'text-blue-600' : 'text-amber-500'}`} />
          <span className="font-medium">{trgmEnabled ? 'Trigram Ready' : 'Trigram Off'}</span>
        </div>

        {/* Live API Pulse */}
        <div className="flex items-center gap-1.5 text-xs">
          <Activity className={`w-3.5 h-3.5 ${apiConnected ? 'text-emerald-500 animate-pulse' : 'text-rose-500'}`} />
          <span className={`font-medium hidden lg:inline ${apiConnected ? 'text-slate-600' : 'text-rose-600'}`}>
            {apiConnected ? 'Online' : 'API Offline'}
          </span>
        </div>

        {/* User Pill / Sign Out */}
        {user && (
          <div className="flex items-center gap-1.5 pl-1.5 border-l border-slate-200">
            <div className="hidden sm:flex flex-col items-end text-right">
              <span className="text-xs font-bold text-slate-800 leading-tight">
                {user.full_name || user.username}
              </span>
              <span className={`text-[10px] font-semibold px-1.5 py-0.2 rounded-sm border ${getRoleBadgeStyle(user.role)}`}>
                {user.role}
              </span>
            </div>

            <div
              className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-xs shadow-xs"
              title={`${user.full_name} (${user.email}) - ${user.role}`}
            >
              {user.full_name ? user.full_name.charAt(0).toUpperCase() : <UserIcon className="w-4 h-4" />}
            </div>

            <button
              onClick={logout}
              title="Sign out"
              className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-slate-100 rounded-lg transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
