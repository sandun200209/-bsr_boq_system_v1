import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Layout/Sidebar';
import { Header } from './components/Layout/Header';
import { DashboardPage } from './pages/DashboardPage';
import { ImportCenterPage } from './pages/ImportCenterPage';
import { RateSearchPage } from './pages/RateSearchPage';
import { CompareRatesPage } from './pages/CompareRatesPage';
import { ReviewQueuePage } from './pages/ReviewQueuePage';
import { SourceFilesPage } from './pages/SourceFilesPage';
import { MasterItemsPage } from './pages/MasterItemsPage';
import { SettingsPage } from './pages/SettingsPage';
import { api } from './api/client';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [reviewCount, setReviewCount] = useState<number>(0);
  const [apiConnected, setApiConnected] = useState<boolean>(true);
  const [dbConnected, setDbConnected] = useState<boolean>(true);
  const [trgmEnabled, setTrgmEnabled] = useState<boolean>(true);
  const [navigationParams, setNavigationParams] = useState<any>(null);

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
    } catch (err) {
      setApiConnected(false);
      setDbConnected(false);
      setTrgmEnabled(false);
    }
  };

  useEffect(() => {
    refreshMetrics();
    const timer = setInterval(refreshMetrics, 15000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    refreshMetrics();
  }, [activeTab]);

  const handleNavigate = (tab: string, params?: any) => {
    setNavigationParams(params || null);
    setActiveTab(tab);
  };

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50 font-sans text-slate-900">
      {/* Sidebar */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={(tab) => {
          setNavigationParams(null);
          setActiveTab(tab);
        }}
        reviewCount={reviewCount}
        apiConnected={apiConnected}
        dbConnected={dbConnected}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Header
          activeTab={activeTab}
          apiConnected={apiConnected}
          dbConnected={dbConnected}
          trgmEnabled={trgmEnabled}
        />

        <main className="flex-1 overflow-y-auto bg-slate-50">
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
            />
          )}
          {activeTab === 'compare' && <CompareRatesPage />}
          {activeTab === 'review' && (
            <ReviewQueuePage
              initialFileId={navigationParams?.source_file_id}
              onRefreshMetrics={refreshMetrics}
            />
          )}
          {activeTab === 'sources' && (
            <SourceFilesPage
              onNavigateToReview={(fileId) => handleNavigate('review', { source_file_id: fileId })}
            />
          )}
          {activeTab === 'master' && <MasterItemsPage />}
          {activeTab === 'settings' && <SettingsPage />}
        </main>
      </div>
    </div>
  );
};

export default App;
