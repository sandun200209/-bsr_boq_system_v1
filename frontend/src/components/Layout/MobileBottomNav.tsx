import React from 'react';
import {
  LayoutDashboard,
  Search,
  GitCompare,
  UploadCloud,
  Menu,
  CheckSquare,
} from 'lucide-react';

interface MobileBottomNavProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onOpenSidebar: () => void;
  reviewCount?: number;
}

export const MobileBottomNav: React.FC<MobileBottomNavProps> = ({
  activeTab,
  setActiveTab,
  onOpenSidebar,
  reviewCount = 0,
}) => {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'search', label: 'Search', icon: Search },
    { id: 'compare', label: 'Compare', icon: GitCompare },
    { id: 'review', label: 'Review', icon: CheckSquare, badge: reviewCount },
    { id: 'import', label: 'Import', icon: UploadCloud },
  ];

  return (
    <div className="lg:hidden fixed bottom-0 left-0 right-0 z-30 bg-slate-900/95 backdrop-blur-md border-t border-slate-800 safe-area-pb">
      <div className="flex items-center justify-around h-15 px-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex-1 flex flex-col items-center justify-center py-1 relative transition-colors ${
                isActive ? 'text-blue-400 font-bold' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <div className="relative">
                <Icon className={`w-5 h-5 ${isActive ? 'scale-110 text-blue-400' : 'text-slate-400'} transition-transform`} />
                {item.badge !== undefined && item.badge > 0 && (
                  <span className="absolute -top-1.5 -right-2 px-1 py-0.2 bg-amber-500 text-slate-950 font-extrabold text-[9px] rounded-full min-w-[14px] text-center leading-tight">
                    {item.badge}
                  </span>
                )}
              </div>
              <span className="text-[10px] tracking-tight mt-0.5">{item.label}</span>
              {isActive && (
                <span className="w-1 h-1 rounded-full bg-blue-400 mt-0.5"></span>
              )}
            </button>
          );
        })}

        {/* More / Menu Button to open sidebar */}
        <button
          onClick={onOpenSidebar}
          className="flex-1 flex flex-col items-center justify-center py-1 text-slate-400 hover:text-slate-200 transition-colors"
        >
          <Menu className="w-5 h-5 text-slate-400" />
          <span className="text-[10px] tracking-tight mt-0.5">More</span>
        </button>
      </div>
    </div>
  );
};
