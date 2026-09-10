import React, { useState, useEffect } from 'react';
import {
  Database,
  ShieldCheck,
  HardDrive,
  Network,
  Copy,
  Check,
  RefreshCw,
} from 'lucide-react';
import { api } from '../api/client';

export const SettingsPage: React.FC = () => {
  const [health, setHealth] = useState<any | null>(null);
  const [dbHealth, setDbHealth] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [copiedCmd, setCopiedCmd] = useState<string | null>(null);

  const checkStatus = async () => {
    try {
      setLoading(true);
      const [h, dbH] = await Promise.all([
        api.getHealth(),
        api.getDatabaseHealth(),
      ]);
      setHealth(h);
      setDbHealth(dbH);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkStatus();
  }, []);

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedCmd(id);
    setTimeout(() => setCopiedCmd(null), 2000);
  };

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-slate-900 tracking-tight">System Settings & Health</h2>
        <p className="text-xs text-slate-500 mt-1">
          Diagnostics, persistent storage paths, LAN connectivity information, and database backup guides.
        </p>
      </div>

      {/* System Health Status Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold uppercase">API Backend</span>
            <div className="p-2 bg-blue-50 rounded-lg text-blue-600">
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </div>
          </div>
          <div className="text-xl font-bold text-slate-900 mt-2">
            {health?.status === 'ok' ? 'Operational' : 'Checking...'}
          </div>
          <div className="text-xs text-slate-400 mt-0.5">
            {health?.app || 'FastAPI Server'} (v{health?.version || '1.0'})
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold uppercase">PostgreSQL Database</span>
            <div className="p-2 bg-emerald-50 rounded-lg text-emerald-600">
              <Database className="w-4 h-4" />
            </div>
          </div>
          <div className="text-xl font-bold text-slate-900 mt-2">
            {dbHealth?.status === 'connected' ? 'Connected (Port 5432)' : 'Unavailable'}
          </div>
          <div className="text-xs text-emerald-600 mt-0.5 font-medium">
            PostgreSQL 16 Alpine
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold uppercase">Trigram Indexing</span>
            <div className="p-2 bg-indigo-50 rounded-lg text-indigo-600">
              <ShieldCheck className="w-4 h-4" />
            </div>
          </div>
          <div className="text-xl font-bold text-slate-900 mt-2">
            {dbHealth?.pg_trgm_enabled ? 'Active (pg_trgm)' : 'Extension Missing'}
          </div>
          <div className="text-xs text-slate-400 mt-0.5">
            GIN Trigram Fast Substring Search
          </div>
        </div>
      </div>

      {/* LAN Office Deployment Guide */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-4">
        <div className="flex items-center gap-2.5 border-b border-slate-100 pb-3">
          <div className="p-2 bg-emerald-50 rounded-xl text-emerald-600">
            <Network className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">Multi-PC Office LAN Configuration</h3>
            <p className="text-xs text-slate-500">Access this BSR system from other Windows PCs on your office Wi-Fi / Ethernet</p>
          </div>
        </div>

        <div className="text-xs text-slate-600 space-y-3">
          <p>
            The BSR Rate Hub is bound to <code className="bg-slate-100 px-1.5 py-0.5 rounded font-mono font-bold text-slate-800">0.0.0.0:8080</code>.
            To connect from another computer in your office:
          </p>

          <ol className="list-decimal list-inside space-y-2 pl-2">
            <li>
              Find this host PC's LAN IP address by running <code className="bg-slate-100 px-1.5 py-0.5 rounded font-mono">ipconfig</code> in Command Prompt (e.g. <code className="bg-slate-100 px-1.5 py-0.5 rounded font-mono font-bold">192.168.1.105</code>).
            </li>
            <li>
              On other office PCs or laptops, open Chrome or Edge and navigate to:
              <div className="mt-1 flex items-center gap-2">
                <code className="bg-slate-900 text-amber-400 px-3 py-1.5 rounded-lg font-mono font-semibold text-xs">
                  http://&lt;HOST_IP&gt;:8080
                </code>
              </div>
            </li>
            <li>
              Ensure Windows Firewall allows inbound connections on TCP Port <strong className="text-slate-800">8080</strong> if prompted.
            </li>
          </ol>
        </div>
      </div>

      {/* Storage and Database Backups */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-4">
        <div className="flex items-center gap-2.5 border-b border-slate-100 pb-3">
          <div className="p-2 bg-blue-50 rounded-xl text-blue-600">
            <HardDrive className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">Persistent Storage & Disaster Recovery</h3>
            <p className="text-xs text-slate-500">Source files and PostgreSQL volumes remain safe during container restarts</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200/80 space-y-2">
            <div className="font-bold text-slate-900 flex items-center justify-between">
              <span>Database & Files Backup</span>
              <button
                onClick={() => copyToClipboard('backup_database.bat', 'backup')}
                className="text-blue-600 hover:text-blue-700 flex items-center gap-1 text-[11px]"
              >
                {copiedCmd === 'backup' ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                <span>Copy Script</span>
              </button>
            </div>
            <p className="text-slate-500 text-[11px]">
              Double-click <code className="font-mono bg-white px-1 py-0.5 rounded border border-slate-200">backup_database.bat</code> in the project folder to create a timestamped SQL dump and file archive in <code className="font-mono">data/backups/</code>.
            </p>
          </div>

          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200/80 space-y-2">
            <div className="font-bold text-slate-900 flex items-center justify-between">
              <span>Database Restore</span>
              <button
                onClick={() => copyToClipboard('restore_database.bat', 'restore')}
                className="text-blue-600 hover:text-blue-700 flex items-center gap-1 text-[11px]"
              >
                {copiedCmd === 'restore' ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                <span>Copy Script</span>
              </button>
            </div>
            <p className="text-slate-500 text-[11px]">
              Run <code className="font-mono bg-white px-1 py-0.5 rounded border border-slate-200">restore_database.bat &lt;backup_file.sql&gt;</code> to restore database tables and original source files.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
