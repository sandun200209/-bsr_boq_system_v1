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
  Network,
  Users,
  LogOut,
  X,
  User as UserIcon,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  reviewCount?: number;
  apiConnected?: boolean;
  dbConnected?: boolean;
  isOpen?: boolean;
  onClose?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  reviewCount = 0,
  apiConnected = true,
  dbConnected = true,
  isOpen = false,
  onClose,
}) => {
  const { user, logout } = useAuth();

  const baseMenuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'import', label: 'Import Center', icon: UploadCloud },
    { id: 'search', label: 'Rate Search', icon: Search },
    { id: 'compare', label: 'Compare Rates', icon: GitCompare },
    { id: 'review', label: 'Review Queue', icon: CheckSquare, badge: reviewCount },
    { id: 'sources', label: 'Source Files', icon: FileText },
    { id: 'master', label: 'Master Items', icon: Layers },
  ];

  // Add User Management for ADMIN only
  if (user?.role === 'ADMIN') {
    baseMenuItems.push({ id: 'users', label: 'Users & Audit', icon: Users, badge: undefined });
  }

  baseMenuItems.push({ id: 'settings', label: 'Settings', icon: SettingsIcon, badge: undefined });

  const getRoleBadgeStyle = (role?: string) => {
    switch (role) {
      case 'ADMIN':
        return 'bg-rose-500/20 text-rose-300 border-rose-500/30';
      case 'MANAGER':
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30';
      case 'USER':
        return 'bg-blue-500/20 text-blue-300 border-blue-500/30';
      case 'VIEWER':
      default:
        return 'bg-slate-700 text-slate-300 border-slate-600';
    }
  };

  const handleSelectTab = (tabId: string) => {
    setActiveTab(tabId);
    if (onClose) {
      onClose();
    }
  };

  return (
    <>
      {/* Mobile Backdrop */}
      <div
        className={`fixed inset-0 bg-slate-950/70 z-40 backdrop-blur-xs lg:hidden transition-opacity duration-300 ${
          isOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
        }`}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Sidebar Drawer */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-slate-900 text-slate-300 flex flex-col flex-shrink-0 min-h-screen border-r border-slate-800 select-none transform transition-transform duration-300 ease-in-out lg:static lg:translate-x-0 ${
          isOpen ? 'translate-x-0 shadow-2xl' : '-translate-x-full'
        }`}
      >
        {/* Brand Header */}
        <div className="p-4 sm:p-5 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20 shrink-0">
              <HardHat className="w-6 h-6" />
            </div>
            <div>
              <div className="font-bold text-white tracking-tight leading-none text-base">BSR Rate Hub</div>
              <div className="text-[10px] text-amber-400 font-medium tracking-wide mt-1 uppercase">Sri Lanka BOQ System</div>
            </div>
          </div>

          {/* Close Button for Mobile */}
          <button
            type="button"
            onClick={onClose}
            className="lg:hidden p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
            title="Close navigation"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {baseMenuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleSelectTab(item.id)}
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

        {/* User Account & Profile Footer */}
        {user && (
          <div className="p-3 mx-3 mb-2 bg-slate-800/80 rounded-xl border border-slate-700/60 flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5 min-w-0">
                <div className="w-8 h-8 rounded-lg bg-blue-500/20 text-blue-400 flex items-center justify-center font-bold text-xs shrink-0 border border-blue-500/30">
                  {user.full_name ? user.full_name.charAt(0).toUpperCase() : <UserIcon className="w-4 h-4" />}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="text-xs font-semibold text-white truncate leading-tight">
                    {user.full_name || user.username}
                  </div>
                  <div className="text-[10px] text-slate-400 font-mono truncate">
                    {user.email}
                  </div>
                </div>
              </div>

              <button
                onClick={logout}
                title="Sign out of system"
                className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-700/60 rounded-lg transition-colors shrink-0"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>

            <div className="flex items-center justify-between pt-1 border-t border-slate-700/50 text-[10px]">
              <span className="text-slate-400">Role:</span>
              <span className={`px-2 py-0.5 rounded-full font-bold border ${getRoleBadgeStyle(user.role)}`}>
                {user.role}
              </span>
            </div>
          </div>
        )}

        {/* LAN Access Badge */}
        <div className="px-3 pb-2">
          <div className="p-2.5 bg-slate-950/40 rounded-lg border border-slate-800 text-[11px]">
            <div className="flex items-center gap-1.5 text-slate-400 mb-0.5">
              <Network className="w-3 h-3 text-emerald-400 shrink-0" />
              <span className="font-semibold text-slate-300">Multi-Device Ready</span>
            </div>
            <p className="text-[10px] text-slate-500 leading-tight">
              Shared cloud/LAN data access active.
            </p>
          </div>
        </div>

        {/* Footer Info */}
        <div className="p-3 border-t border-slate-800/80 text-[10px] text-slate-500 flex justify-between items-center">
          <span>BSR v1.0 • {apiConnected ? 'Online' : 'Offline'}</span>
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
          />
        </div>
      </aside>
    </>
  );
};
