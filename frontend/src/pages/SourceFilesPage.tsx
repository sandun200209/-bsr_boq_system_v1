import React, { useState, useEffect } from 'react';
import {
  Download,
  ExternalLink,
  RefreshCw,
  HardDrive,
} from 'lucide-react';
import { api } from '../api/client';
import { SourceFile } from '../types';

interface SourceFilesPageProps {
  onNavigateToReview?: (fileId: number) => void;
}

export const SourceFilesPage: React.FC<SourceFilesPageProps> = ({
  onNavigateToReview,
}) => {
  const [files, setFiles] = useState<SourceFile[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const loadFiles = async () => {
    try {
      setLoading(true);
      const data = await api.getDocuments({ limit: 100 });
      setFiles(data);
    } catch (err) {
      console.error('Failed to load source documents:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFiles();
  }, []);

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Source Files Archive</h2>
          <p className="text-xs text-slate-500 mt-1">
            Permanent document storage preserving all historical revisions and cryptographic SHA-256 hashes.
          </p>
        </div>

        <button
          onClick={loadFiles}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-white border border-slate-300 rounded-lg hover:bg-slate-50 shadow-xs"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Files</span>
        </button>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-slate-100 text-slate-700 font-bold uppercase border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Document / SHA-256</th>
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
                    <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-blue-600" />
                    <span>Loading document repository...</span>
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
                    {/* Filename & Hash */}
                    <td className="py-3.5 px-4">
                      <div className="font-bold text-slate-900 text-sm truncate max-w-sm" title={file.original_filename}>
                        {file.original_filename}
                      </div>
                      <div className="text-[11px] text-slate-500 font-mono mt-0.5">
                        {(file.file_size / (1024 * 1024)).toFixed(2)} MB • {file.file_type.toUpperCase()}
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
                      <div className="flex items-center justify-center gap-2">
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
                            className="text-[10px] font-bold px-2 py-1 bg-amber-500 hover:bg-amber-600 text-white rounded-md shadow-2xs"
                          >
                            Review
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
