import React, { useState, useEffect } from 'react';
import {
  Download,
  ExternalLink,
  RefreshCw,
  HardDrive,
  Cloud,
  Trash2,
  AlertCircle,
  CheckCircle,
} from 'lucide-react';
import { api } from '../api/client';
import { SourceFile } from '../types';
import { SECTORS, SECTOR_BADGE_CLASSES } from '../constants/sriLanka';
import { useAuth } from '../context/AuthContext';

interface SourceFilesPageProps {
  onNavigateToReview?: (fileId: number) => void;
}

export const SourceFilesPage: React.FC<SourceFilesPageProps> = ({
  onNavigateToReview,
}) => {
  const { user } = useAuth();
  const [files, setFiles] = useState<SourceFile[]>([]);
  const [sectorFilter, setSectorFilter] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const loadFiles = async () => {
    try {
      setLoading(true);
      setActionError(null);
      const data = await api.getDocuments({
        sector: sectorFilter || undefined,
        limit: 100,
      });
      setFiles(data);
    } catch (err: any) {
      console.error('Failed to load source documents:', err);
      setActionError(err.message || 'Failed to load source files.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFiles();
  }, [sectorFilter]);

  const handleDelete = async (file: SourceFile) => {
    if (user?.role !== 'ADMIN') {
      alert('Only administrators can delete archive documents.');
      return;
    }

    const confirmMsg = `Permanently delete "${file.original_filename}" and all associated rate items? This action cannot be undone.`;
    if (!window.confirm(confirmMsg)) {
      return;
    }

    try {
      setActionError(null);
      await api.deleteDocument(file.id);
      setActionSuccess(`Document "${file.original_filename}" deleted successfully.`);
      await loadFiles();
    } catch (err: any) {
      setActionError(err.message || 'Failed to delete document.');
    }
  };

  return (
    <div className="p-4 sm:p-8 max-w-7xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <span>Source Files Archive</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Permanent document storage preserving all historical revisions, SHA-256 hashes, and cloud storage pointers.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={sectorFilter}
            onChange={(e) => setSectorFilter(e.target.value)}
            className="text-xs rounded-xl border border-slate-300 py-2 px-3 bg-white focus:outline-none focus:ring-1 focus:ring-blue-600 font-medium text-slate-800"
          >
            <option value="">All Sectors</option>
            {SECTORS.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>

          <button
            onClick={loadFiles}
            className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold bg-white border border-slate-300 rounded-xl hover:bg-slate-50 shadow-xs transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Notifications */}
      {actionError && (
        <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-xl flex items-center gap-3 text-xs sm:text-sm text-rose-700">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-500" />
          <span>{actionError}</span>
          <button onClick={() => setActionError(null)} className="ml-auto text-rose-500 hover:text-rose-700">
            ×
          </button>
        </div>
      )}
      {actionSuccess && (
        <div className="p-3.5 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center gap-3 text-xs sm:text-sm text-emerald-700">
          <CheckCircle className="w-4 h-4 shrink-0 text-emerald-500" />
          <span>{actionSuccess}</span>
          <button onClick={() => setActionSuccess(null)} className="ml-auto text-emerald-500 hover:text-emerald-700">
            ×
          </button>
        </div>
      )}

      {/* Table Container */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-slate-100/80 text-slate-700 font-bold uppercase border-b border-slate-200 text-[11px] tracking-wider">
              <tr>
                <th className="py-3 px-4">Document / Storage</th>
                <th className="py-3 px-3">Province & District</th>
                <th className="py-3 px-3">Year / Revision</th>
                <th className="py-3 px-3">Dataset & VAT</th>
                <th className="py-3 px-3 text-right">Items Detected</th>
                <th className="py-3 px-3">Status</th>
                <th className="py-3 px-4 text-center">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-blue-600" />
                    <span className="text-xs">Loading document repository...</span>
                  </td>
                </tr>
              ) : files.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400">
                    <HardDrive className="w-8 h-8 mx-auto mb-2 text-slate-300" />
                    <span className="font-semibold text-slate-700 block text-sm">No source files yet</span>
                    <span className="text-xs text-slate-400">Upload documents in the Import Center to begin.</span>
                  </td>
                </tr>
              ) : (
                files.map((file) => (
                  <tr key={file.id} className="hover:bg-slate-50 transition-colors">
                    {/* Filename, Hash & Storage Provider */}
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-2 flex-wrap">
                        <div className="font-bold text-slate-900 text-sm truncate max-w-xs sm:max-w-sm" title={file.original_filename}>
                          {file.original_filename}
                        </div>
                        {file.sector && (
                          <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold border ${SECTOR_BADGE_CLASSES[file.sector] || 'bg-slate-100 text-slate-700'}`}>
                            {file.rate_system || file.sector.split(' ')[0]}
                          </span>
                        )}
                        {/* Cloud vs Local Badge */}
                        <span
                          className={`inline-flex items-center gap-1 px-1.5 py-0.2 rounded text-[10px] font-bold border ${
                            file.storage_provider === 'supabase'
                              ? 'bg-purple-50 text-purple-700 border-purple-200'
                              : 'bg-slate-100 text-slate-600 border-slate-200'
                          }`}
                        >
                          {file.storage_provider === 'supabase' ? (
                            <>
                              <Cloud className="w-3 h-3 text-purple-600" />
                              <span>Cloud Supabase</span>
                            </>
                          ) : (
                            <>
                              <HardDrive className="w-3 h-3 text-slate-500" />
                              <span>Server Local</span>
                            </>
                          )}
                        </span>
                      </div>

                      <div className="text-[11px] text-slate-500 font-mono mt-0.5 flex items-center gap-2">
                        <span>{(file.file_size / (1024 * 1024)).toFixed(2)} MB</span>
                        <span>•</span>
                        <span>{file.file_type.toUpperCase()}</span>
                        {file.uploaded_by_email && (
                          <>
                            <span>•</span>
                            <span className="text-slate-400">By {file.uploaded_by_email}</span>
                          </>
                        )}
                      </div>

                      <div className="text-[10px] text-slate-400 font-mono mt-0.5 truncate max-w-xs" title={file.sha256_hash}>
                        SHA-256: {file.sha256_hash.substring(0, 16)}...
                      </div>
                    </td>

                    {/* Region */}
                    <td className="py-3.5 px-3">
                      <div className="font-semibold text-slate-800">{file.district}</div>
                      <div className="text-[11px] text-slate-500">{file.province} Province</div>
                    </td>

                    {/* Year & Revision */}
                    <td className="py-3.5 px-3">
                      <div className="font-semibold text-slate-800">{file.year}</div>
                      <div className="text-[11px] text-slate-500">{file.revision}</div>
                    </td>

                    {/* Dataset & VAT */}
                    <td className="py-3.5 px-3">
                      <div className="font-medium text-slate-700">{file.dataset_type}</div>
                      <div className="text-[11px] text-slate-500">{file.vat_basis}</div>
                    </td>

                    {/* Items Counts */}
                    <td className="py-3.5 px-3 text-right font-mono">
                      <div className="font-bold text-slate-900">{file.total_rows_detected} rows</div>
                      <div className="text-[10px] text-emerald-600 font-semibold">{file.valid_rows} valid</div>
                      {file.review_rows > 0 && (
                        <div className="text-[10px] text-amber-600 font-semibold">{file.review_rows} in review</div>
                      )}
                    </td>

                    {/* Status */}
                    <td className="py-3.5 px-3">
                      <span
                        className={`inline-block px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                          file.import_status === 'COMPLETED'
                            ? 'bg-emerald-100 text-emerald-800'
                            : file.import_status === 'READY_FOR_REVIEW'
                            ? 'bg-amber-100 text-amber-800'
                            : file.import_status === 'OCR_REQUIRED'
                            ? 'bg-purple-100 text-purple-800'
                            : 'bg-rose-100 text-rose-800'
                        }`}
                      >
                        {file.import_status.replace(/_/g, ' ')}
                      </span>
                    </td>

                    {/* Actions */}
                    <td className="py-3.5 px-4 text-center">
                      <div className="flex items-center justify-center gap-1.5">
                        <a
                          href={`/api/documents/${file.id}/download`}
                          target="_blank"
                          rel="noreferrer"
                          title="Download original file"
                          className="p-1.5 text-slate-500 hover:text-blue-600 hover:bg-slate-100 rounded-lg transition-colors"
                        >
                          <Download className="w-4 h-4" />
                        </a>

                        <a
                          href={`/api/documents/${file.id}/view`}
                          target="_blank"
                          rel="noreferrer"
                          title="View document inline"
                          className="p-1.5 text-slate-500 hover:text-blue-600 hover:bg-slate-100 rounded-lg transition-colors"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </a>

                        {file.review_rows > 0 && onNavigateToReview && (
                          <button
                            onClick={() => onNavigateToReview(file.id)}
                            title="Inspect review queue for this file"
                            className="text-[10px] font-bold px-2 py-1 bg-amber-500 hover:bg-amber-600 text-white rounded-md shadow-2xs transition-colors"
                          >
                            Review
                          </button>
                        )}

                        {/* Admin Delete Action */}
                        {user?.role === 'ADMIN' && (
                          <button
                            onClick={() => handleDelete(file)}
                            title="Permanently delete document (Admin only)"
                            className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
