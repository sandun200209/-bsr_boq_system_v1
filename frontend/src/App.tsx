import React, { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { LoginPage } from './pages/LoginPage';
import { Sidebar } from './components/Layout/Sidebar';
import { Header } from './components/Layout/Header';
import { MobileBottomNav } from './components/Layout/MobileBottomNav';
import { DashboardPage } from './pages/DashboardPage';
import { ImportCenterPage } from './pages/ImportCenterPage';
import { RateSearchPage } from './pages/RateSearchPage';
import { CompareRatesPage } from './pages/CompareRatesPage';
import { ReviewQueuePage } from './pages/ReviewQueuePage';
import { SourceFilesPage } from './pages/SourceFilesPage';
import { MasterItemsPage } from './pages/MasterItemsPage';
import { UserManagementPage } from './pages/UserManagementPage';
import { SettingsPage } from './pages/SettingsPage';
import { ExportReportPage } from './pages/ExportReportPage';
import { api } from './api/client';
import { HardHat, Loader2 } from 'lucide-react';

const MainApp: React.FC = () => {
  const { user, isLoading } = useAuth();
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [reviewCount, setReviewCount] = useState<number>(0);
  const [apiConnected, setApiConnected] = useState<boolean>(true);
  const [dbConnected, setDbConnected] = useState<boolean>(true);
  const [trgmEnabled, setTrgmEnabled] = useState<boolean>(true);
  const [navigationParams, setNavigationParams] = useState<any>(null);
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(false);

  // Check health and review queue count
  const refreshMetrics = async () => {
    try {
      const [h, dash, dbH] = await Promise.all([
        api.getHealth().catch(() => null),
        api.getDashboard().catch(() => null),
        api.getDatabaseHealth().catch(() => null),
      ]);

      setApiConnected(!!h && h.status === 'ok');

      if (dash) {
        setReviewCount(dash.items_needing_review);
      }
      if (dbH) {
        setDbConnected(dbH.status === 'connected');
        setTrgmEnabled(!!dbH.pg_trgm_enabled);
      } else {
        setDbConnected(false);
        setTrgmEnabled(false);
      }
    } catch {
      setApiConnected(false);
      setDbConnected(false);
      setTrgmEnabled(false);
    }
  };

  useEffect(() => {
    if (user) {
      refreshMetrics();
      const timer = setInterval(refreshMetrics, 15000);
      return () => clearInterval(timer);
    }
  }, [user]);

  useEffect(() => {
    if (user) {
      refreshMetrics();
    }
  }, [activeTab, user]);

  const handleNavigate = (tab: string, params?: any) => {
    setNavigationParams(params || null);
    setActiveTab(tab);
    setSidebarOpen(false);
  };

  // Loading state while restoring auth session
  if (isLoading) {
    return (
      <div className="h-screen w-screen bg-slate-950 flex flex-col items-center justify-center text-white">
        <div className="w-14 h-14 rounded-2xl bg-blue-600 flex items-center justify-center shadow-xl shadow-blue-500/20 mb-4 animate-pulse">
          <HardHat className="w-8 h-8 text-white" />
        </div>
        <div className="flex items-center gap-2 text-sm text-slate-300 font-medium">
          <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
          <span>Connecting to BSR Central System...</span>
        </div>
      </div>
    );
  }

  // Not logged in -> Show Login Page
  if (!user) {
    return <LoginPage />;
  }

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50 font-sans text-slate-900">
      {/* Sidebar with mobile drawer toggle */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={(tab) => {
          setNavigationParams(null);
          setActiveTab(tab);
          setSidebarOpen(false);
        }}
        reviewCount={reviewCount}
        apiConnected={apiConnected}
        dbConnected={dbConnected}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Header
          activeTab={activeTab}
          apiConnected={apiConnected}
          dbConnected={dbConnected}
          trgmEnabled={trgmEnabled}
          onOpenSidebar={() => setSidebarOpen(true)}
        />

        <main className="flex-1 overflow-y-auto bg-slate-50 pb-18 lg:pb-0">
          {activeTab === 'dashboard' && (
            <DashboardPage onNavigate={handleNavigate} />
          )}
          {activeTab === 'import' && (
            <ImportCenterPage
              onNavigate={handleNavigate}
              onRefreshMetrics={refreshMetrics}
            />
          )}
          {activeTab === 'search' && (
            <RateSearchPage
              initialFilters={navigationParams}
              onViewSource={(fileId) => handleNavigate('sources', { fileId })}
              onNavigate={handleNavigate}
            />
          )}
          {activeTab === 'compare' && <CompareRatesPage />}
          {activeTab === 'review' && (
            <ReviewQueuePage
              initialFileId={navigationParams?.source_file_id}
              onRefreshMetrics={refreshMetrics}
              onNavigate={handleNavigate}
            />
          )}
          {activeTab === 'export' && <ExportReportPage />}
          {activeTab === 'sources' && (
            <SourceFilesPage
              onNavigateToReview={(fileId) => handleNavigate('review', { source_file_id: fileId })}
            />
          )}
          {activeTab === 'master' && <MasterItemsPage />}
          {activeTab === 'users' && user?.role === 'ADMIN' && <UserManagementPage />}
          {activeTab === 'settings' && <SettingsPage />}
        </main>
      </div>

      {/* Mobile Bottom Navigation Bar (< lg screens) */}
      <MobileBottomNav
        activeTab={activeTab}
        setActiveTab={(tab) => {
          setNavigationParams(null);
          setActiveTab(tab);
        }}
        onOpenSidebar={() => setSidebarOpen(true)}
        reviewCount={reviewCount}
      />
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  );
};

export default App;
