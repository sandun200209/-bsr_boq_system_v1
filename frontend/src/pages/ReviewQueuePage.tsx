import React, { useState, useEffect } from 'react';
import {
  CheckSquare,
  Check,
  X,
  Edit2,
  RefreshCw,
  Lock,
  FileSpreadsheet,
  Layers,
} from 'lucide-react';
import { api } from '../api/client';
import { RateItem } from '../types';
import { SECTORS, SECTOR_BADGE_CLASSES } from '../constants/sriLanka';
import { useAuth } from '../context/AuthContext';
import { CESMMMappingModal } from '../components/CESMM/CESMMMappingModal';

interface ReviewQueuePageProps {
  initialFileId?: number;
  onRefreshMetrics?: () => void;
  onNavigate?: (tab: string, params?: any) => void;
}

export const ReviewQueuePage: React.FC<ReviewQueuePageProps> = ({
  initialFileId,
  onRefreshMetrics,
  onNavigate,
}) => {
  const { user, hasRole } = useAuth();
  const canReview = hasRole(['ADMIN', 'MANAGER']);

  const [items, setItems] = useState<RateItem[]>([]);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [statusFilter, setStatusFilter] = useState<string>('NEEDS_REVIEW');
  const [sectorFilter, setSectorFilter] = useState<string>('');
  const [editingItem, setEditingItem] = useState<RateItem | null>(null);
  const [cesmmModalItem, setCesmmModalItem] = useState<RateItem | null>(null);

  // Edit Form Fields
  const [editCode, setEditCode] = useState<string>('');
  const [editDesc, setEditDesc] = useState<string>('');
  const [editUnit, setEditUnit] = useState<string>('');
  const [editRate, setEditRate] = useState<string>('');
  const [editCategory, setEditCategory] = useState<string>('');
  const [editSector, setEditSector] = useState<string>('Building Works');

  const loadQueue = async () => {
    try {
      setLoading(true);
      const res = await api.getReviewQueue({
        source_file_id: initialFileId,
        sector: sectorFilter || undefined,
        status: statusFilter === 'ALL' ? undefined : statusFilter,
        page_size: 100,
      });
      setItems(res.items);
      setSelectedIds([]);
    } catch (err) {
      console.error('Failed to load review queue:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQueue();
  }, [statusFilter, sectorFilter, initialFileId]);

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedIds(items.map((i) => i.id));
    } else {
      setSelectedIds([]);
    }
  };

  const toggleSelect = (id: number) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const handleApproveSingle = async (id: number) => {
    try {
      await api.approveReviewItem(id);
      setItems((prev) => prev.filter((i) => i.id !== id));
      if (onRefreshMetrics) onRefreshMetrics();
    } catch (err: any) {
      alert(err.message || 'Failed to approve item');
    }
  };

  const handleRejectSingle = async (id: number) => {
    try {
      await api.rejectReviewItem(id);
      setItems((prev) => prev.filter((i) => i.id !== id));
      if (onRefreshMetrics) onRefreshMetrics();
    } catch (err: any) {
      alert(err.message || 'Failed to reject item');
    }
  };

  const handleBulkAction = async (action: 'APPROVE' | 'REJECT') => {
    if (selectedIds.length === 0) return;
    try {
      const res = await api.bulkReviewAction(selectedIds, action);
      alert(res.message);
      setItems((prev) => prev.filter((i) => !selectedIds.includes(i.id)));
      setSelectedIds([]);
      if (onRefreshMetrics) onRefreshMetrics();
    } catch (err: any) {
      alert(err.message || 'Bulk action failed');
    }
  };

  const startEditing = (item: RateItem) => {
    setEditingItem(item);
    setEditCode(item.item_code || '');
    setEditDesc(item.description || '');
    setEditUnit(item.unit || '');
    setEditRate(item.rate !== null && item.rate !== undefined ? item.rate.toString() : '');
    setEditCategory(item.category_name || '');
    setEditSector(item.sector || 'Building Works');
  };

  const saveEdit = async () => {
    if (!editingItem) return;
    try {
      const updated = await api.updateReviewItem(editingItem.id, {
        item_code: editCode,
        description: editDesc,
        unit: editUnit,
        rate: parseFloat(editRate) || 0,
        category_name: editCategory,
        sector: editSector,
        validation_status: 'VALID',
        validation_notes: null,
      });
      setItems((prev) => prev.map((i) => (i.id === updated.id ? updated : i)));
      setEditingItem(null);
      if (onRefreshMetrics) onRefreshMetrics();
    } catch (err: any) {
      alert(err.message || 'Failed to update item');
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {!canReview && (
        <div className="p-3.5 bg-amber-50 border border-amber-200 rounded-xl text-amber-800 text-xs sm:text-sm flex items-center gap-3">
          <Lock className="w-5 h-5 text-amber-600 shrink-0" />
          <span>
            <strong>Read-Only Inspection Mode:</strong> You are signed in with the {user?.role || 'VIEWER'} role. Approving, rejecting, or editing queue items requires MANAGER or ADMIN privileges.
          </span>
        </div>
      )}

      {/* Header & Bulk Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">Review Queue</h2>
          <p className="text-xs text-slate-500 mt-1">
            Questionable rows identified during extraction. Review, correct, or reject items before final storage.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3 flex-wrap">
          <select
            value={sectorFilter}
            onChange={(e) => setSectorFilter(e.target.value)}
            className="text-xs rounded-lg border border-slate-300 py-2 px-3 bg-white focus:outline-none focus:ring-2 focus:ring-blue-600 font-medium text-slate-800"
          >
            <option value="">All Sectors</option>
            {SECTORS.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs rounded-lg border border-slate-300 py-2 px-3 bg-white focus:outline-none focus:ring-2 focus:ring-blue-600 font-medium"
          >
            <option value="NEEDS_REVIEW">Needs Review</option>
            <option value="VALID">Valid (Pending Approval)</option>
            <option value="REJECTED">Rejected</option>
            <option value="ALL">All Items</option>
          </select>

          <button
            disabled={selectedIds.length === 0 || !canReview}
            onClick={() => handleBulkAction('APPROVE')}
            className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold transition-all ${
              selectedIds.length === 0 || !canReview
                ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-xs'
            }`}
          >
            <Check className="w-3.5 h-3.5" />
            <span>Approve Selected ({selectedIds.length})</span>
          </button>

          <button
            disabled={selectedIds.length === 0 || !canReview}
            onClick={() => handleBulkAction('REJECT')}
            className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold transition-all ${
              selectedIds.length === 0 || !canReview
                ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                : 'bg-rose-600 hover:bg-rose-500 text-white shadow-xs'
            }`}
          >
            <X className="w-3.5 h-3.5" />
            <span>Reject Selected ({selectedIds.length})</span>
          </button>

          <button
            onClick={() => onNavigate && onNavigate('export', { source_file_id: initialFileId, sector: sectorFilter })}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold bg-teal-600 hover:bg-teal-500 text-white shadow-xs transition-all cursor-pointer"
            title="Export items to QS Master Excel / PDF format"
          >
            <FileSpreadsheet className="w-3.5 h-3.5" />
            <span>Export Master BOQ</span>
          </button>
        </div>
      </div>

      {/* Editable Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-slate-100 text-slate-700 font-bold uppercase sticky top-0 z-10 border-b border-slate-200 shadow-2xs">
              <tr>
                <th className="py-3 px-4 w-10 text-center">
                  <input
                    type="checkbox"
                    checked={items.length > 0 && selectedIds.length === items.length}
                    onChange={(e) => handleSelectAll(e.target.checked)}
                    className="rounded text-blue-600 focus:ring-blue-500"
                  />
                </th>
                <th className="py-3 px-3 w-28">Status / Quality</th>
                <th className="py-3 px-3 w-24">Code</th>
                <th className="py-3 px-4 min-w-[280px]">Description</th>
                <th className="py-3 px-3 w-16">Unit</th>
                <th className="py-3 px-4 text-right w-28">Rate (LKR)</th>
                <th className="py-3 px-3 min-w-[140px]">Category</th>
                <th className="py-3 px-3 min-w-[140px]">Source</th>
                <th className="py-3 px-4 text-center w-36">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-400">
                    <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-blue-600" />
                    <span>Loading review queue...</span>
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-400">
                    <CheckSquare className="w-8 h-8 mx-auto mb-2 text-emerald-500" />
                    <span className="font-semibold text-slate-700 block text-sm">Review Queue Empty</span>
                    <span className="text-xs text-slate-400">No questionable rate items requiring manual verification.</span>
                  </td>
                </tr>
              ) : (
                items.map((item) => {
                  const isSelected = selectedIds.includes(item.id);
                  const isUncertain = item.confidence_score < 0.8 || item.validation_status === 'NEEDS_REVIEW';

                  return (
                    <tr
                      key={item.id}
                      className={`transition-colors ${
                        isSelected
                          ? 'bg-blue-50/70'
                          : isUncertain
                          ? 'bg-amber-50/20 hover:bg-amber-50/40'
                          : 'hover:bg-slate-50'
                      }`}
                    >
                      {/* Checkbox */}
                      <td className="py-3 px-4 text-center">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleSelect(item.id)}
                          className="rounded text-blue-600 focus:ring-blue-500"
                        />
                      </td>

                      {/* Status & Confidence */}
                      <td className="py-3 px-3">
                        <span
                          className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            item.validation_status === 'APPROVED'
                              ? 'bg-emerald-100 text-emerald-800'
                              : item.validation_status === 'VALID'
                              ? 'bg-blue-100 text-blue-800'
                              : item.validation_status === 'REJECTED'
                              ? 'bg-rose-100 text-rose-800'
                              : 'bg-amber-100 text-amber-800'
                          }`}
                        >
                          {item.validation_status.replace(/_/g, ' ')}
                        </span>
                        {item.validation_notes && (
                          <div className="text-[10px] text-amber-700 mt-1 font-medium leading-tight">
                            {item.validation_notes}
                          </div>
                        )}
                        <div className="text-[10px] text-slate-400 mt-0.5">
                          Conf: {Math.round(item.confidence_score * 100)}%
                        </div>
                      </td>

                      {/* Code */}
                      <td className="py-3 px-3 font-mono font-bold text-blue-700">
                        {item.item_code || <span className="text-rose-400 italic">None</span>}
                      </td>

                      {/* Description */}
                      <td className="py-3 px-4 text-slate-900 leading-relaxed">
                        <div className="font-medium">{item.description}</div>
                        <div className="flex flex-wrap items-center gap-1.5 mt-1">
                          {item.sector && (
                            <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold border ${SECTOR_BADGE_CLASSES[item.sector] || 'bg-slate-100 text-slate-700'}`}>
                              {item.rate_system || item.sector.split(' ')[0]}
                            </span>
                          )}
                          {item.category_name && (
                            <span className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 text-[10px] font-semibold">
                              {item.category_name}
                            </span>
                          )}
                          {/* CESMM Badges */}
                          {item.cesmm_sections && item.cesmm_sections.length > 0 && (() => {
                            const sorted = [...item.cesmm_sections].sort((a, b) => (b.is_primary ? 1 : 0) - (a.is_primary ? 1 : 0));
                            const primary = sorted[0];
                            const extraCount = sorted.length - 1;
                            return (
                              <button
                                type="button"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setCesmmModalItem(item);
                                }}
                                className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200 hover:bg-indigo-100 transition-colors"
                                title={`CESMM-SL Section ${primary.section_no} (${primary.section_code}): ${primary.name || primary.section_name}${extraCount > 0 ? ` +${extraCount} more` : ''}`}
                              >
                                <Layers className="w-2.5 h-2.5 text-indigo-500 shrink-0" />
                                <span>CESMM {primary.section_no} · {primary.section_code}</span>
                                {extraCount > 0 && (
                                  <span className="bg-indigo-200 text-indigo-800 rounded px-1 text-[9px] font-bold">
                                    +{extraCount}
                                  </span>
                                )}
                              </button>
                            );
                          })()}
                        </div>
                        {item.raw_text && item.raw_text !== item.description && (
                          <div className="text-[10px] text-slate-400 font-mono mt-1 truncate max-w-sm" title={item.raw_text}>
                            Raw: {item.raw_text}
                          </div>
                        )}
                      </td>

                      {/* Unit */}
                      <td className="py-3 px-3 font-mono font-medium text-slate-700">
                        {item.unit || <span className="text-rose-400 italic">-</span>}
                      </td>

                      {/* Rate */}
                      <td className="py-3 px-4 text-right font-mono font-bold text-slate-900 text-sm">
                        {item.rate !== null && item.rate !== undefined ? (
                          item.rate.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
                        ) : (
                          <span className="text-rose-500 italic">Null</span>
                        )}
                      </td>

                      {/* Category */}
                      <td className="py-3 px-3 text-slate-600">
                        {item.category_name || '-'}
                      </td>

                      {/* Source */}
                      <td className="py-3 px-3 text-slate-500 text-[11px]">
                        <div className="truncate max-w-[120px]" title={item.original_filename || ''}>
                          {item.original_filename || 'Source'}
                        </div>
                        <div className="text-[10px] text-slate-400 font-mono">
                          {item.source_page ? `P.${item.source_page}` : item.source_sheet ? `${item.source_sheet} R.${item.source_row}` : ''}
                        </div>
                      </td>

                      {/* Row Action Buttons */}
                      <td className="py-3 px-4 text-center">
                        <div className="flex items-center justify-center gap-1.5">
                          <button
                            onClick={() => setCesmmModalItem(item)}
                            title="Classify under CESMM-SL Work Sections"
                            className="p-1.5 text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                          >
                            <Layers className="w-3.5 h-3.5" />
                          </button>

                          <button
                            disabled={!canReview}
                            onClick={() => startEditing(item)}
                            title={canReview ? "Edit row details" : "Editing requires Manager or Admin"}
                            className={`p-1.5 rounded-lg transition-colors ${
                              !canReview
                                ? 'text-slate-300 cursor-not-allowed'
                                : 'text-slate-500 hover:text-blue-600 hover:bg-slate-100'
                            }`}
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                          </button>

                          <button
                            disabled={!canReview}
                            onClick={() => handleApproveSingle(item.id)}
                            title={canReview ? "Approve row" : "Approval requires Manager or Admin"}
                            className={`p-1.5 rounded-lg transition-all border ${
                              !canReview
                                ? 'text-slate-300 border-slate-200 cursor-not-allowed'
                                : 'text-emerald-600 hover:text-white hover:bg-emerald-600 border-emerald-200 hover:border-emerald-600'
                            }`}
                          >
                            <Check className="w-3.5 h-3.5" />
                          </button>

                          <button
                            disabled={!canReview}
                            onClick={() => handleRejectSingle(item.id)}
                            title={canReview ? "Reject row" : "Rejection requires Manager or Admin"}
                            className={`p-1.5 rounded-lg transition-all border ${
                              !canReview
                                ? 'text-slate-300 border-slate-200 cursor-not-allowed'
                                : 'text-rose-600 hover:text-white hover:bg-rose-600 border-rose-200 hover:border-rose-600'
                            }`}
                          >
                            <X className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Inline Edit Modal */}
      {editingItem && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl p-6 max-w-lg w-full space-y-4">
            <h3 className="text-base font-bold text-slate-900 border-b border-slate-100 pb-3">
              Edit Rate Item #{editingItem.id}
            </h3>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Item Code</label>
                <input
                  type="text"
                  value={editCode}
                  onChange={(e) => setEditCode(e.target.value)}
                  className="w-full p-2 border border-slate-300 rounded-lg font-mono focus:ring-2 focus:ring-blue-600"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Description</label>
                <textarea
                  rows={3}
                  value={editDesc}
                  onChange={(e) => setEditDesc(e.target.value)}
                  className="w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-600"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Unit</label>
                  <input
                    type="text"
                    value={editUnit}
                    onChange={(e) => setEditUnit(e.target.value)}
                    className="w-full p-2 border border-slate-300 rounded-lg font-mono focus:ring-2 focus:ring-blue-600"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Rate (LKR)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={editRate}
                    onChange={(e) => setEditRate(e.target.value)}
                    className="w-full p-2 border border-slate-300 rounded-lg font-mono font-bold focus:ring-2 focus:ring-blue-600"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Category</label>
                  <input
                    type="text"
                    value={editCategory}
                    onChange={(e) => setEditCategory(e.target.value)}
                    className="w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-600"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Sector</label>
                  <select
                    value={editSector}
                    onChange={(e) => setEditSector(e.target.value)}
                    className="w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-600 bg-white"
                  >
                    {SECTORS.map((s) => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-4 border-t border-slate-100">
              <button
                onClick={() => setEditingItem(null)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={saveEdit}
                className="px-4 py-2 text-xs font-bold bg-blue-600 hover:bg-blue-500 text-white rounded-lg shadow-xs"
              >
                Save & Mark Valid
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CESMM Classification Modal */}
      {cesmmModalItem && (
        <CESMMMappingModal
          item={cesmmModalItem}
          onClose={() => setCesmmModalItem(null)}
          onUpdated={() => {
            loadQueue();
          }}
        />
      )}
    </div>
  );
};
