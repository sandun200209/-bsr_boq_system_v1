import React from 'react';
import {
  LayoutDashboard,
  UploadCloud,
  Search,
  GitCompare,
  CheckSquare,
  FileText,
  Layers,
  Settings as SettingsIcon,
  HardHat,
  Network
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  reviewCount?: number;
  apiConnected?: boolean;
  dbConnected?: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  reviewCount = 0,
  apiConnected = true,
  dbConnected = true,
}) => {
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'import', label: 'Import Center', icon: UploadCloud },
    { id: 'search', label: 'Rate Search', icon: Search },
    { id: 'compare', label: 'Compare Rates', icon: GitCompare },
    { id: 'review', label: 'Review Queue', icon: CheckSquare, badge: reviewCount },
    { id: 'sources', label: 'Source Files', icon: FileText },
    { id: 'master', label: 'Master Items', icon: Layers },
    { id: 'settings', label: 'Settings', icon: SettingsIcon },
  ];

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col flex-shrink-0 min-h-screen border-r border-slate-800 select-none">
      {/* Brand Header */}
      <div className="p-5 border-b border-slate-800 flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
          <HardHat className="w-6 h-6" />
        </div>
        <div>
          <div className="font-bold text-white tracking-tight leading-none text-base">BSR Rate Hub</div>
          <div className="text-[11px] text-amber-400 font-medium tracking-wide mt-1 uppercase">Sri Lanka BOQ System</div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? 'bg-blue-600 text-white shadow-sm font-semibold'
                  : 'text-slate-300 hover:bg-slate-800/80 hover:text-white'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </div>
              {item.badge !== undefined && item.badge > 0 && (
                <span
                  className={`text-xs px-2 py-0.5 rounded-full font-bold ${
                    isActive ? 'bg-amber-400 text-slate-950' : 'bg-amber-500/20 text-amber-400'
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* LAN Access Badge */}
      <div className="p-3 mx-3 mb-4 bg-slate-800/60 rounded-lg border border-slate-800 text-xs">
        <div className="flex items-center gap-2 text-slate-400 mb-1">
          <Network className="w-3.5 h-3.5 text-emerald-400" />
          <span className="font-medium text-slate-300">Office LAN Ready</span>
        </div>
        <p className="text-[11px] text-slate-500 leading-tight">
          Accessible across your local network via Port <span className="text-amber-400 font-mono font-semibold">8080</span>.
        </p>
      </div>

      {/* Footer Info */}
      <div className="p-4 border-t border-slate-800/80 text-[11px] text-slate-500 flex justify-between items-center">
        <span>BSR v1.0 • Desktop ({apiConnected ? 'Online' : 'Offline'})</span>
        <span
          className={`inline-block w-2 h-2 rounded-full transition-colors ${
            !apiConnected
              ? 'bg-rose-500'
              : !dbConnected
              ? 'bg-amber-400'
              : 'bg-emerald-500'
          }`}
          title={
            !apiConnected
              ? 'Backend API offline'
              : !dbConnected
              ? 'Database disconnected'
              : 'System online and connected'
          }
        ></span>
      </div>
    </aside>
  );
};
