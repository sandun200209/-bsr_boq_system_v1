import React, { useEffect, useState } from 'react';
import {
  FileText,
  Layers,
  MapPin,
  AlertCircle,
  TrendingUp,
  UploadCloud,
  Search,
  CheckCircle2,
  ArrowRight
} from 'lucide-react';
import { api } from '../api/client';
import { DashboardMetrics } from '../types';

interface DashboardPageProps {
  onNavigate: (tab: string) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ onNavigate }) => {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const data = await api.getDashboard();
      setMetrics(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard metrics');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
          <span className="text-sm text-slate-500 font-medium">Loading Sri Lanka BSR metrics...</span>
        </div>
      </div>
    );
  }

  if (error || !metrics) {
    return (
      <div className="p-8">
        <div className="bg-rose-50 border border-rose-200 text-rose-800 p-4 rounded-xl flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-rose-600" />
            <span className="text-sm font-medium">{error || 'Unable to connect to BSR database.'}</span>
          </div>
          <button
            onClick={loadDashboard}
            className="px-3 py-1.5 bg-rose-600 text-white rounded-lg text-xs font-semibold hover:bg-rose-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Welcome Banner with Quick Actions */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-blue-950 rounded-2xl p-6 text-white shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full bg-blue-500/20 text-blue-300 text-xs font-semibold mb-2">
            <span>Sri Lanka Construction Hub</span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight">Building Schedule of Rates Repository</h2>
          <p className="text-slate-300 text-sm mt-1 max-w-xl">
            Upload provincial BSR booklets, extract structured work items, verify rate variations,
            and perform fast cross-district price comparisons.
          </p>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <button
            onClick={() => onNavigate('import')}
            className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm rounded-xl transition-all shadow-sm"
          >
            <UploadCloud className="w-4 h-4" />
            <span>Upload Document</span>
          </button>
          <button
            onClick={() => onNavigate('search')}
            className="flex items-center gap-2 px-4 py-2.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white font-semibold text-sm rounded-xl transition-all"
          >
            <Search className="w-4 h-4" />
            <span>Search Rates</span>
          </button>
        </div>
      </div>

      {/* KPI Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Total Rates */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs hover:border-slate-300 transition-all">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Rate Items</span>
            <div className="p-2 bg-blue-50 rounded-lg text-blue-600">
              <Layers className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-2">
            {metrics.total_rate_items.toLocaleString()}
          </div>
          <div className="text-xs text-slate-500 mt-1 flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
            <span>{metrics.approved_items.toLocaleString()} approved</span>
          </div>
        </div>

        {/* Source Files */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs hover:border-slate-300 transition-all">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold uppercase tracking-wider">Source Files</span>
            <div className="p-2 bg-emerald-50 rounded-lg text-emerald-600">
              <FileText className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-2">
            {metrics.source_files_count.toLocaleString()}
          </div>
          <div className="text-xs text-slate-500 mt-1">
            <span>Permanently stored</span>
          </div>
        </div>

        {/* Provinces */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs hover:border-slate-300 transition-all">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold uppercase tracking-wider">Provinces</span>
            <div className="p-2 bg-indigo-50 rounded-lg text-indigo-600">
              <MapPin className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-2">
            {metrics.provinces_count} / 9
          </div>
          <div className="text-xs text-slate-500 mt-1">
            <span>Covered nationwide</span>
          </div>
        </div>

        {/* Districts */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs hover:border-slate-300 transition-all">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold uppercase tracking-wider">Districts</span>
            <div className="p-2 bg-cyan-50 rounded-lg text-cyan-600">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-2">
            {metrics.districts_count} / 25
          </div>
          <div className="text-xs text-slate-500 mt-1">
            <span>Active district books</span>
          </div>
        </div>

        {/* Needs Review */}
        <div
          onClick={() => onNavigate('review')}
          className="bg-white p-5 rounded-xl border border-amber-200 shadow-xs hover:border-amber-400 transition-all cursor-pointer bg-amber-50/20"
        >
          <div className="flex items-center justify-between text-amber-700">
            <span className="text-xs font-semibold uppercase tracking-wider">Needs Review</span>
            <div className="p-2 bg-amber-100 rounded-lg text-amber-700">
              <AlertCircle className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-amber-900 mt-2">
            {metrics.items_needing_review.toLocaleString()}
          </div>
          <div className="text-xs text-amber-600 font-medium mt-1 flex items-center gap-1">
            <span>Inspect queue &rarr;</span>
          </div>
        </div>
      </div>

      {/* Grid: Recent Uploads & Provincial Coverage */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Uploads Table (2 cols) */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-xs p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-slate-900">Recent Uploads & Imports</h3>
              <p className="text-xs text-slate-500">Latest documents processed by the extraction engine</p>
            </div>
            <button
              onClick={() => onNavigate('sources')}
              className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1"
            >
              <span>View All</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {metrics.recent_uploads.length === 0 ? (
            <div className="text-center py-10 border border-dashed border-slate-200 rounded-xl">
              <FileText className="w-8 h-8 text-slate-300 mx-auto mb-2" />
              <p className="text-sm font-medium text-slate-600">No BSR documents uploaded yet.</p>
              <button
                onClick={() => onNavigate('import')}
                className="mt-3 text-xs px-3 py-1.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700"
              >
                Upload First Document
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase">
                  <tr>
                    <th className="py-2.5 px-3">File / Details</th>
                    <th className="py-2.5 px-3">Region</th>
                    <th className="py-2.5 px-3">Year / Rev</th>
                    <th className="py-2.5 px-3">Items</th>
                    <th className="py-2.5 px-3 text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {metrics.recent_uploads.map((file) => (
                    <tr key={file.id} className="hover:bg-slate-50/80">
                      <td className="py-3 px-3">
                        <div className="font-semibold text-slate-900 truncate max-w-xs" title={file.original_filename}>
                          {file.original_filename}
                        </div>
                        <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                          {(file.file_size / (1024 * 1024)).toFixed(2)} MB • {file.file_type.toUpperCase()}
                        </div>
                      </td>
                      <td className="py-3 px-3">
                        <div className="font-medium text-slate-800">{file.district}</div>
                        <div className="text-[11px] text-slate-500">{file.province}</div>
                      </td>
                      <td className="py-3 px-3">
                        <div className="font-semibold text-slate-800">{file.year}</div>
                        <div className="text-[11px] text-slate-500">{file.revision}</div>
                      </td>
                      <td className="py-3 px-3">
                        <div className="font-semibold text-slate-900">{file.total_rows_detected} rows</div>
                        <div className="text-[11px] text-emerald-600">{file.valid_rows} valid</div>
                      </td>
                      <td className="py-3 px-3 text-right">
                        <span
                          className={`inline-block px-2 py-0.5 rounded-full font-semibold text-[10px] ${
                            file.import_status === 'COMPLETED'
                              ? 'bg-emerald-100 text-emerald-800'
                              : file.import_status === 'READY_FOR_REVIEW'
                              ? 'bg-amber-100 text-amber-800'
                              : file.import_status === 'OCR_REQUIRED'
                              ? 'bg-purple-100 text-purple-800'
                              : 'bg-slate-100 text-slate-700'
                          }`}
                        >
                          {file.import_status.replace(/_/g, ' ')}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Provincial Distribution Card (1 col) */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-6 flex flex-col justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-900">Provincial Coverage</h3>
            <p className="text-xs text-slate-500 mb-4">Rate item distribution across Sri Lanka</p>

            {metrics.province_breakdown.length === 0 ? (
              <p className="text-xs text-slate-400 py-6 text-center">No provincial data available yet.</p>
            ) : (
              <div className="space-y-3">
                {metrics.province_breakdown.map((item) => {
                  const maxCount = Math.max(...metrics.province_breakdown.map((b) => b.count), 1);
                  const pct = Math.round((item.count / maxCount) * 100);
                  return (
                    <div key={item.province} className="text-xs">
                      <div className="flex justify-between font-medium text-slate-700 mb-1">
                        <span>{item.province}</span>
                        <span className="font-semibold text-slate-900">{item.count.toLocaleString()}</span>
                      </div>
                      <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                        <div
                          className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                          style={{ width: `${pct}%` }}
                        ></div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          <div className="mt-6 pt-4 border-t border-slate-100">
            <button
              onClick={() => onNavigate('compare')}
              className="w-full py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-lg text-xs font-semibold transition-all flex items-center justify-center gap-1.5"
            >
              <span>Compare Provincial Rates</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
