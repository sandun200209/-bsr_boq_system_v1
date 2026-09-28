import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  BookOpen,
  ChevronRight,
  Download,
  Pencil,
  Trash2,
  Copy,
  History,
  Plus,
  Search,
  X,
  CheckSquare,
  Square,
  AlertTriangle,
  Eye,
  RefreshCw,
  FileSpreadsheet,
  FileText,
  ArrowLeft,
  Layers,
  ZapIcon,
} from 'lucide-react';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import type {
  CanonicalBSRPart,
  PartLibraryItem,
  CrossYearRateItem,
  CrossYearPartData,
  ProjectPartSelection,
  ProjectPartItem,
  DuplicateWarning,
  ProjectPartItemHistoryRecord,
} from '../types';

// ── Helpers ──────────────────────────────────────────────────────────────────

const fmtNum = (n?: number | null) =>
  n === undefined || n === null ? '–' : n.toLocaleString('en-LK', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const fmt0 = (n?: number | null) =>
  n === undefined || n === null ? '–' : n.toLocaleString('en-LK', { maximumFractionDigits: 0 });

// ── Duplicate Warning Modal ───────────────────────────────────────────────────

interface DuplicateModalProps {
  warnings: DuplicateWarning[];
  onReplace: (existingId: number, newItemId: number) => void;
  onKeepBoth: (itemId: number) => void;
  onCancel: () => void;
  pendingIds: number[];
}

const DuplicateWarningModal: React.FC<DuplicateModalProps> = ({
  warnings,
  onReplace,
  onKeepBoth,
  onCancel,
  pendingIds,
}) => (
  <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
    <div className="bg-white rounded-2xl shadow-2xl w-full max-w-xl p-6 mx-4">
      <div className="flex items-center gap-3 mb-4">
        <AlertTriangle className="w-6 h-6 text-amber-500 shrink-0" />
        <h2 className="text-lg font-bold text-slate-800">Duplicate Item Detected</h2>
      </div>

      <div className="space-y-4 max-h-72 overflow-y-auto mb-4">
        {warnings.map((w, i) => (
          <div key={i} className="border border-amber-200 bg-amber-50 rounded-lg p-4 text-sm">
            <p className="font-semibold text-amber-800 mb-2">
              Master Item #{w.master_item_id || 'N/A'} already selected (BSR {w.existing_rate_year})
            </p>
            <p className="text-slate-600">
              New selection uses BSR <span className="font-bold">{w.new_rate_year}</span>.
            </p>
            <div className="flex gap-2 mt-3">
              <button
                onClick={() => onReplace(w.existing_selection_item_id, w.new_rate_item_id)}
                className="flex-1 px-3 py-1.5 bg-amber-500 text-white rounded-lg text-xs font-semibold hover:bg-amber-600 transition-colors"
              >
                Replace with {w.new_rate_year} rate
              </button>
              <button
                onClick={() => onKeepBoth(w.new_rate_item_id)}
                className="flex-1 px-3 py-1.5 bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold hover:bg-slate-300 transition-colors"
              >
                Keep Both
              </button>
            </div>
          </div>
        ))}
      </div>

      <button
        onClick={onCancel}
        className="w-full px-4 py-2 border border-slate-300 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors"
      >
        Cancel
      </button>
    </div>
  </div>
);

// ── Edit Item Modal ────────────────────────────────────────────────────────────

interface EditItemModalProps {
  item: ProjectPartItem;
  userRole: string;
  onSave: (itemId: number, data: Partial<ProjectPartItem>) => Promise<void>;
  onClose: () => void;
}

const EditItemModal: React.FC<EditItemModalProps> = ({ item, userRole, onSave, onClose }) => {
  const [form, setForm] = useState({
    item_no: item.item_no || '',
    project_description: item.project_description,
    project_unit: item.project_unit,
    quantity: item.quantity,
    adjustment_percent: item.adjustment_percent,
    adopted_rate: item.adopted_rate,
    rate_justification: item.rate_justification || '',
    remarks: item.remarks || '',
    sort_order: item.sort_order,
  });
  const [unitWarning, setUnitWarning] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canEditRate = ['MANAGER', 'ADMIN'].includes(userRole);
  const canEditUnit = ['MANAGER', 'ADMIN'].includes(userRole);

  const computedAdoptedRate =
    form.adopted_rate !== item.original_rate
      ? form.adopted_rate
      : item.original_rate * (1 + form.adjustment_percent / 100);

  const amount = form.quantity * form.adopted_rate;

  const handleUnitChange = (val: string) => {
    if (val !== item.original_unit) setUnitWarning(true);
    setForm((f) => ({ ...f, project_unit: val }));
  };

  const handleSave = async () => {
    if (form.adopted_rate !== item.original_rate && !form.rate_justification.trim()) {
      setError('Rate Justification is required when changing the adopted rate.');
      return;
    }
    if (unitWarning && !form.remarks.trim()) {
      setError('Please add a remark explaining why the unit was changed.');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await onSave(item.id, form);
      onClose();
    } catch (e: any) {
      setError(e.message || 'Failed to save');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 overflow-y-auto py-8">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl mx-4 p-6">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-bold text-slate-800">Edit Project Item</h2>
          <button onClick={onClose} className="p-1.5 text-slate-400 hover:text-slate-700 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* BSR Source info */}
        <div className="mb-5 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm">
          <div className="font-semibold text-blue-800 mb-1">BSR Source (read-only)</div>
          <div className="text-blue-700">
            <span className="font-mono mr-3">{item.original_code || '—'}</span>
            <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full mr-2">
              {item.rate_source_year}
            </span>
            {item.rate_source_book}
          </div>
          <div className="text-xs text-blue-600 mt-1 truncate">{item.original_description}</div>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg text-sm flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
            {error}
          </div>
        )}

        {unitWarning && (
          <div className="mb-4 p-3 bg-amber-50 border border-amber-200 text-amber-700 rounded-lg text-sm">
            <AlertTriangle className="w-4 h-4 inline mr-1" />
            <strong>Warning:</strong> Changing the unit may invalidate the original BSR rate. Please add a remark.
          </div>
        )}

        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Item No.</label>
            <input
              type="text"
              value={form.item_no}
              onChange={(e) => setForm((f) => ({ ...f, item_no: e.target.value }))}
              className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">
              Unit {!canEditUnit && <span className="text-slate-400">(read-only)</span>}
            </label>
            {canEditUnit ? (
              <input
                type="text"
                value={form.project_unit}
                onChange={(e) => handleUnitChange(e.target.value)}
                className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
              />
            ) : (
              <div className="border border-slate-200 bg-slate-50 rounded-lg px-3 py-2 text-sm text-slate-600">
                {form.project_unit}
              </div>
            )}
          </div>
        </div>

        <div className="mb-4">
          <label className="block text-xs font-semibold text-slate-600 mb-1">Project Description</label>
          <textarea
            value={form.project_description}
            onChange={(e) => setForm((f) => ({ ...f, project_description: e.target.value }))}
            rows={3}
            className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm resize-none"
          />
        </div>

        <div className="grid grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Quantity</label>
            <input
              type="number"
              step="0.01"
              value={form.quantity}
              onChange={(e) => setForm((f) => ({ ...f, quantity: parseFloat(e.target.value) || 0 }))}
              className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Original Rate</label>
            <div className="border border-slate-200 bg-slate-50 rounded-lg px-3 py-2 text-sm text-slate-500">
              {fmtNum(item.original_rate)}
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Adjustment %</label>
            <input
              type="number"
              step="0.1"
              value={form.adjustment_percent}
              onChange={(e) => setForm((f) => ({ ...f, adjustment_percent: parseFloat(e.target.value) || 0 }))}
              className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
              disabled={!canEditRate}
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">
              Adopted Rate {!canEditRate && <span className="text-slate-400">(read-only)</span>}
            </label>
            {canEditRate ? (
              <input
                type="number"
                step="0.01"
                value={form.adopted_rate}
                onChange={(e) => setForm((f) => ({ ...f, adopted_rate: parseFloat(e.target.value) || 0 }))}
                className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
              />
            ) : (
              <div className="border border-slate-200 bg-slate-50 rounded-lg px-3 py-2 text-sm text-slate-600">
                {fmtNum(form.adopted_rate)}
              </div>
            )}
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Amount (auto)</label>
            <div className="border border-slate-200 bg-emerald-50 rounded-lg px-3 py-2 text-sm text-emerald-700 font-semibold">
              LKR {fmtNum(amount)}
            </div>
          </div>
        </div>

        <div className="mb-4">
          <label className="block text-xs font-semibold text-slate-600 mb-1">
            Rate Justification {form.adopted_rate !== item.original_rate && <span className="text-rose-500">*</span>}
          </label>
          <textarea
            value={form.rate_justification}
            onChange={(e) => setForm((f) => ({ ...f, rate_justification: e.target.value }))}
            rows={2}
            className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm resize-none"
            placeholder="Explain why the rate was adjusted..."
          />
        </div>

        <div className="mb-6">
          <label className="block text-xs font-semibold text-slate-600 mb-1">Remarks</label>
          <input
            type="text"
            value={form.remarks}
            onChange={(e) => setForm((f) => ({ ...f, remarks: e.target.value }))}
            className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
          />
        </div>

        <div className="flex gap-3">
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex-1 px-4 py-2.5 bg-blue-600 text-white rounded-xl text-sm font-semibold hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {saving ? 'Saving…' : 'Save Changes'}
          </button>
          <button
            onClick={onClose}
            className="px-4 py-2.5 border border-slate-300 rounded-xl text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

// ── Edit History Modal ─────────────────────────────────────────────────────────

const HistoryModal: React.FC<{ itemId: number; onClose: () => void }> = ({ itemId, onClose }) => {
  const [history, setHistory] = useState<ProjectPartItemHistoryRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getPartItemHistory(itemId)
      .then(setHistory)
      .catch(() => setHistory([]))
      .finally(() => setLoading(false));
  }, [itemId]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg mx-4 p-6 max-h-[80vh] flex flex-col">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-bold text-slate-800">Edit History</h2>
          <button onClick={onClose} className="p-1.5 text-slate-400 hover:text-slate-700 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>
        {loading ? (
          <div className="text-center text-slate-500 py-8">Loading…</div>
        ) : history.length === 0 ? (
          <div className="text-center text-slate-400 py-8">No edit history for this item.</div>
        ) : (
          <div className="overflow-y-auto flex-1 space-y-3">
            {history.map((h) => (
              <div key={h.id} className="border border-slate-200 rounded-lg p-3 text-sm">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-semibold text-slate-700 capitalize">{h.field_changed.replace(/_/g, ' ')}</span>
                  <span className="text-xs text-slate-400">{new Date(h.changed_at).toLocaleString()}</span>
                </div>
                <div className="flex gap-2 text-xs">
                  <span className="text-rose-600 line-through">{h.old_value || '—'}</span>
                  <span className="text-slate-400">→</span>
                  <span className="text-emerald-700">{h.new_value || '—'}</span>
                </div>
                {h.changed_by && <div className="text-xs text-slate-400 mt-1">by {h.changed_by}</div>}
                {h.reason && <div className="text-xs text-blue-600 mt-1 italic">{h.reason}</div>}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// ── Selected Part BOQ Workspace ───────────────────────────────────────────────

interface PartBOQWorkspaceProps {
  selection: ProjectPartSelection;
  userRole: string;
  onBack: () => void;
  onRefresh: () => void;
}

const PartBOQWorkspace: React.FC<PartBOQWorkspaceProps> = ({
  selection,
  userRole,
  onBack,
  onRefresh,
}) => {
  const [editItem, setEditItem] = useState<ProjectPartItem | null>(null);
  const [historyItemId, setHistoryItemId] = useState<number | null>(null);
  const [removing, setRemoving] = useState<number | null>(null);
  const [exporting, setExporting] = useState<'excel' | 'pdf' | null>(null);

  const subtotal = useMemo(
    () => selection.items.reduce((s, it) => s + (it.quantity * it.adopted_rate), 0),
    [selection.items]
  );

  const handleSaveEdit = async (itemId: number, data: Partial<ProjectPartItem>) => {
    await api.updatePartItem(itemId, data);
    onRefresh();
  };

  const handleRemove = async (itemId: number) => {
    if (!confirm('Remove this item from the project? The original BSR record will NOT be deleted.')) return;
    setRemoving(itemId);
    try {
      await api.removePartItem(itemId);
      onRefresh();
    } finally {
      setRemoving(null);
    }
  };

  const handleDuplicate = async (itemId: number) => {
    await api.duplicatePartItem(itemId);
    onRefresh();
  };

  const handleExport = async (type: 'excel' | 'pdf') => {
    setExporting(type);
    try {
      if (type === 'excel') await api.downloadPartExcel(selection.id);
      else await api.downloadPartPdf(selection.id);
    } finally {
      setExporting(null);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-white sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="p-2 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h2 className="font-bold text-slate-800">{selection.name}</h2>
            <p className="text-xs text-slate-500">
              {selection.items.length} items · Subtotal: LKR {fmtNum(subtotal)}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleExport('excel')}
            disabled={exporting !== null}
            className="flex items-center gap-1.5 px-3 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 disabled:opacity-50 transition-colors"
          >
            <FileSpreadsheet className="w-4 h-4" />
            {exporting === 'excel' ? 'Exporting…' : 'Excel'}
          </button>
          <button
            onClick={() => handleExport('pdf')}
            disabled={exporting !== null}
            className="flex items-center gap-1.5 px-3 py-2 bg-rose-600 text-white rounded-lg text-sm font-medium hover:bg-rose-700 disabled:opacity-50 transition-colors"
          >
            <FileText className="w-4 h-4" />
            {exporting === 'pdf' ? 'Exporting…' : 'PDF'}
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto px-4 py-4">
        {selection.items.length === 0 ? (
          <div className="text-center text-slate-400 py-20">No items in this selection. Go back to add rate items.</div>
        ) : (
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="bg-slate-800 text-white">
                <th className="px-3 py-2 text-left text-xs">No.</th>
                <th className="px-3 py-2 text-left text-xs">BSR Ref</th>
                <th className="px-3 py-2 text-left text-xs w-64">Description</th>
                <th className="px-3 py-2 text-center text-xs">Unit</th>
                <th className="px-3 py-2 text-right text-xs">Qty</th>
                <th className="px-3 py-2 text-right text-xs">Orig. Rate</th>
                <th className="px-3 py-2 text-right text-xs">Adj %</th>
                <th className="px-3 py-2 text-right text-xs">Adopted Rate</th>
                <th className="px-3 py-2 text-right text-xs">Amount (LKR)</th>
                <th className="px-3 py-2 text-center text-xs">Year</th>
                <th className="px-3 py-2 text-left text-xs">Source</th>
                <th className="px-3 py-2 text-center text-xs">Actions</th>
              </tr>
            </thead>
            <tbody>
              {[...selection.items]
                .sort((a, b) => a.sort_order - b.sort_order)
                .map((item, idx) => (
                  <tr
                    key={item.id}
                    className={`border-b border-slate-100 hover:bg-slate-50 ${
                      item.is_modified ? 'bg-amber-50' : idx % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'
                    }`}
                  >
                    <td className="px-3 py-2 text-slate-500 text-xs">{item.item_no || idx + 1}</td>
                    <td className="px-3 py-2 font-mono text-xs text-slate-700">{item.original_code || '—'}</td>
                    <td className="px-3 py-2">
                      <div className="text-xs text-slate-800 leading-relaxed">
                        {item.project_description}
                      </div>
                      {item.is_modified && (
                        <span className="inline-block mt-1 text-[10px] px-1.5 py-0.5 bg-amber-100 text-amber-700 rounded-full font-semibold">
                          Modified from BSR Source
                        </span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-center text-xs text-slate-600">{item.project_unit}</td>
                    <td className="px-3 py-2 text-right text-xs tabular-nums">{fmtNum(item.quantity)}</td>
                    <td className="px-3 py-2 text-right text-xs tabular-nums text-slate-500">{fmtNum(item.original_rate)}</td>
                    <td className="px-3 py-2 text-right text-xs tabular-nums">{item.adjustment_percent.toFixed(1)}%</td>
                    <td className="px-3 py-2 text-right text-xs tabular-nums font-medium">{fmtNum(item.adopted_rate)}</td>
                    <td className="px-3 py-2 text-right text-xs tabular-nums font-semibold text-emerald-700">
                      {fmtNum(item.quantity * item.adopted_rate)}
                    </td>
                    <td className="px-3 py-2 text-center">
                      <span className="text-[10px] px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full font-semibold">
                        {item.rate_source_year}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-xs text-slate-500 max-w-28 truncate">
                      {item.rate_source_district || item.rate_source_book || '—'}
                    </td>
                    <td className="px-3 py-2">
                      <div className="flex items-center gap-1 justify-center">
                        <button
                          onClick={() => setEditItem(item)}
                          className="p-1 text-slate-400 hover:text-blue-600 rounded transition-colors"
                          title="Edit item"
                        >
                          <Pencil className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleDuplicate(item.id)}
                          className="p-1 text-slate-400 hover:text-emerald-600 rounded transition-colors"
                          title="Duplicate item"
                        >
                          <Copy className="w-3.5 h-3.5" />
                        </button>
                        {['MANAGER', 'ADMIN'].includes(userRole) && (
                          <button
                            onClick={() => setHistoryItemId(item.id)}
                            className="p-1 text-slate-400 hover:text-purple-600 rounded transition-colors"
                            title="View edit history"
                          >
                            <History className="w-3.5 h-3.5" />
                          </button>
                        )}
                        <button
                          onClick={() => handleRemove(item.id)}
                          disabled={removing === item.id}
                          className="p-1 text-slate-400 hover:text-rose-600 rounded disabled:opacity-50 transition-colors"
                          title="Remove from project"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
            </tbody>
            <tfoot>
              <tr className="bg-slate-100 font-bold">
                <td colSpan={8} className="px-3 py-3 text-right text-sm text-slate-700">SUBTOTAL</td>
                <td className="px-3 py-3 text-right text-sm text-emerald-800 tabular-nums">LKR {fmtNum(subtotal)}</td>
                <td colSpan={3} />
              </tr>
            </tfoot>
          </table>
        )}
      </div>

      {editItem && (
        <EditItemModal
          item={editItem}
          userRole={userRole}
          onSave={handleSaveEdit}
          onClose={() => setEditItem(null)}
        />
      )}
      {historyItemId && (
        <HistoryModal itemId={historyItemId} onClose={() => setHistoryItemId(null)} />
      )}
    </div>
  );
};

// ── Part Cross-Year Viewer ─────────────────────────────────────────────────────

interface CrossYearViewerProps {
  part: CanonicalBSRPart;
  onBack: () => void;
  onOpenBOQ: (selectionId: number) => void;
}

const CrossYearViewer: React.FC<CrossYearViewerProps> = ({ part, onBack, onOpenBOQ }) => {
  const { user } = useAuth();
  const [data, setData] = useState<CrossYearPartData | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeYear, setActiveYear] = useState<number | null>(null);
  const [search, setSearch] = useState('');
  const [district, setDistrict] = useState('');
  const [vat_basis, setVatBasis] = useState('');
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [creatingSelection, setCreatingSelection] = useState(false);
  const [duplicateWarnings, setDuplicateWarnings] = useState<DuplicateWarning[]>([]);
  const [pendingSelectionId, setPendingSelectionId] = useState<number | null>(null);
  const [pendingIds, setPendingIds] = useState<number[]>([]);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.getPartCrossYear(part.id, {
        search: search || undefined,
        district: district || undefined,
        vat_basis: vat_basis || undefined,
        years: activeYear ? [activeYear] : undefined,
        page_size: 500,
      });
      setData(result);
      if (result.available_years.length > 0 && !activeYear) {
        setActiveYear(result.available_years[result.available_years.length - 1]);
      }
    } catch (e: any) {
      setError(e.message || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }, [part.id, search, district, vat_basis, activeYear]);

  useEffect(() => {
    loadData();
  }, [part.id, district, vat_basis]);

  const visibleItems: CrossYearRateItem[] = useMemo(() => {
    if (!data) return [];
    if (activeYear && data.by_year[activeYear]) return data.by_year[activeYear];
    return Object.values(data.by_year).flat();
  }, [data, activeYear]);

  const filteredItems = useMemo(() => {
    if (!search.trim()) return visibleItems;
    const s = search.toLowerCase();
    return visibleItems.filter(
      (it) =>
        it.item_code?.toLowerCase().includes(s) ||
        it.description?.toLowerCase().includes(s)
    );
  }, [visibleItems, search]);

  const toggleAll = () => {
    if (selected.size === filteredItems.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(filteredItems.map((it) => it.id)));
    }
  };

  const handleAddToSelection = async () => {
    if (selected.size === 0) return;
    setCreatingSelection(true);
    setError(null);
    try {
      const sel = await api.createPartSelection(part.id, {});
      const ids = Array.from(selected);
      const result = await api.addItemsToSelection(sel.id, ids, false);

      if (result.warnings.length > 0) {
        setDuplicateWarnings(result.warnings);
        setPendingSelectionId(sel.id);
        setPendingIds(ids);
        return;
      }

      onOpenBOQ(sel.id);
    } catch (e: any) {
      setError(e.message || 'Failed to create selection');
    } finally {
      setCreatingSelection(false);
    }
  };

  const handleDupReplace = async (existingId: number, newItemId: number) => {
    if (!pendingSelectionId) return;
    await api.addItemsToSelection(pendingSelectionId, [newItemId], false, [existingId]);
    setDuplicateWarnings((prev) => prev.filter((w) => w.new_rate_item_id !== newItemId));
    if (duplicateWarnings.length <= 1) onOpenBOQ(pendingSelectionId);
  };

  const handleDupKeepBoth = async (newItemId: number) => {
    if (!pendingSelectionId) return;
    await api.addItemsToSelection(pendingSelectionId, [newItemId], true);
    setDuplicateWarnings((prev) => prev.filter((w) => w.new_rate_item_id !== newItemId));
    if (duplicateWarnings.length <= 1) onOpenBOQ(pendingSelectionId);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 px-6 py-4 sticky top-0 z-10">
        <div className="flex items-center gap-3 mb-3">
          <button
            onClick={onBack}
            className="p-2 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h2 className="font-bold text-slate-800">
              Part {part.part_no} — {part.part_name}
            </h2>
            <p className="text-xs text-slate-500">Select items from different years to build your BOQ</p>
          </div>
        </div>

        {/* Year tabs */}
        {data && data.available_years.length > 0 && (
          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() => { setActiveYear(null); loadData(); }}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                !activeYear
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              All Years
            </button>
            {data.available_years.map((yr) => (
              <button
                key={yr}
                onClick={() => setActiveYear(yr)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  activeYear === yr
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {yr} ({fmt0(data.by_year[yr]?.length)})
              </button>
            ))}
          </div>
        )}

        {/* Filters & search */}
        <div className="flex gap-3 mt-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search item code or description…"
              className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-lg text-sm"
            />
          </div>
          <input
            type="text"
            value={district}
            onChange={(e) => setDistrict(e.target.value)}
            onBlur={loadData}
            placeholder="District"
            className="w-36 border border-slate-300 rounded-lg px-3 py-2 text-sm"
          />
          <select
            value={vat_basis}
            onChange={(e) => { setVatBasis(e.target.value); }}
            className="w-40 border border-slate-300 rounded-lg px-3 py-2 text-sm"
          >
            <option value="">All VAT Basis</option>
            <option value="Without VAT">Without VAT</option>
            <option value="With VAT">With VAT</option>
          </select>
        </div>
      </div>

      {/* Selection bar */}
      {selected.size > 0 && (
        <div className="bg-blue-600 text-white px-6 py-3 flex items-center justify-between">
          <span className="text-sm font-medium">{selected.size} item{selected.size !== 1 ? 's' : ''} selected</span>
          <div className="flex gap-2">
            <button
              onClick={() => setSelected(new Set())}
              className="px-3 py-1.5 bg-white/20 hover:bg-white/30 rounded-lg text-sm transition-colors"
            >
              Clear
            </button>
            <button
              onClick={handleAddToSelection}
              disabled={creatingSelection}
              className="px-4 py-1.5 bg-white text-blue-700 font-semibold rounded-lg text-sm hover:bg-blue-50 disabled:opacity-70 transition-colors"
            >
              {creatingSelection ? 'Creating BOQ…' : 'Build Selected Part BOQ →'}
            </button>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="mx-6 mt-4 p-3 bg-rose-50 border border-rose-200 text-rose-700 text-sm rounded-lg">
          {error}
        </div>
      )}

      {/* Items table */}
      <div className="flex-1 overflow-auto px-4 py-4">
        {loading ? (
          <div className="text-center text-slate-400 py-20">Loading rate items…</div>
        ) : filteredItems.length === 0 ? (
          <div className="text-center text-slate-400 py-20">
            No items found for Part {part.part_no} with the current filters.
          </div>
        ) : (
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="bg-slate-700 text-white">
                <th className="px-3 py-2 w-10">
                  <button onClick={toggleAll}>
                    {selected.size === filteredItems.length ? (
                      <CheckSquare className="w-4 h-4" />
                    ) : (
                      <Square className="w-4 h-4" />
                    )}
                  </button>
                </th>
                <th className="px-3 py-2 text-left text-xs">Year</th>
                <th className="px-3 py-2 text-left text-xs">District</th>
                <th className="px-3 py-2 text-left text-xs">Code</th>
                <th className="px-3 py-2 text-left text-xs">Description</th>
                <th className="px-3 py-2 text-center text-xs">Unit</th>
                <th className="px-3 py-2 text-right text-xs">Rate (LKR)</th>
                <th className="px-3 py-2 text-center text-xs">VAT</th>
                <th className="px-3 py-2 text-center text-xs">Revision</th>
              </tr>
            </thead>
            <tbody>
              {filteredItems.map((item) => {
                const isSel = selected.has(item.id);
                return (
                  <tr
                    key={item.id}
                    onClick={() =>
                      setSelected((prev) => {
                        const next = new Set(prev);
                        if (next.has(item.id)) next.delete(item.id);
                        else next.add(item.id);
                        return next;
                      })
                    }
                    className={`border-b border-slate-100 cursor-pointer transition-colors ${
                      isSel ? 'bg-blue-50 border-blue-200' : 'hover:bg-slate-50'
                    }`}
                  >
                    <td className="px-3 py-2 text-center">
                      {isSel ? (
                        <CheckSquare className="w-4 h-4 text-blue-600 inline" />
                      ) : (
                        <Square className="w-4 h-4 text-slate-300 inline" />
                      )}
                    </td>
                    <td className="px-3 py-2">
                      <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full font-semibold">
                        {item.year}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-xs text-slate-600">{item.district}</td>
                    <td className="px-3 py-2 font-mono text-xs text-slate-700">{item.item_code || '—'}</td>
                    <td className="px-3 py-2 text-xs text-slate-800">{item.description || '—'}</td>
                    <td className="px-3 py-2 text-center text-xs text-slate-600">{item.unit || '—'}</td>
                    <td className="px-3 py-2 text-right text-sm font-semibold tabular-nums text-slate-800">
                      {fmtNum(item.rate)}
                    </td>
                    <td className="px-3 py-2 text-center text-xs text-slate-500">
                      {item.vat_basis?.replace('Without ', 'Ex ')}
                    </td>
                    <td className="px-3 py-2 text-center text-xs text-slate-500">{item.revision}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Duplicate Warning Modal */}
      {duplicateWarnings.length > 0 && pendingSelectionId && (
        <DuplicateWarningModal
          warnings={duplicateWarnings}
          pendingIds={pendingIds}
          onReplace={handleDupReplace}
          onKeepBoth={handleDupKeepBoth}
          onCancel={() => {
            setDuplicateWarnings([]);
            setPendingSelectionId(null);
          }}
        />
      )}
    </div>
  );
};

// ── Parts Library Grid ─────────────────────────────────────────────────────────

interface PartsLibraryProps {
  onSelectPart: (part: CanonicalBSRPart) => void;
  onOpenBOQ: (selectionId: number) => void;
}

const PartsLibrary: React.FC<PartsLibraryProps> = ({ onSelectPart, onOpenBOQ }) => {
  const [parts, setParts] = useState<PartLibraryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [district, setDistrict] = useState('');
  const [classifying, setClassifying] = useState(false);
  const [classifyResult, setClassifyResult] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const data = await api.getPartsLibrary({ district: district || undefined });
      setParts(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [district]);

  const handleClassify = async () => {
    setClassifying(true);
    setClassifyResult(null);
    try {
      const r = await api.classifyItems('BSR', false);
      setClassifyResult(`Classified: ${r.mapped} mapped, ${r.needs_review} needs review, ${r.unchanged} unchanged`);
      await load();
    } catch (e: any) {
      setClassifyResult('Error: ' + e.message);
    } finally {
      setClassifying(false);
    }
  };

  const availableYears = useMemo(() => {
    const ySet = new Set<number>();
    parts.forEach((p) => Object.keys(p.year_availability).forEach((y) => ySet.add(Number(y))));
    return Array.from(ySet).sort();
  }, [parts]);

  const filteredParts = useMemo(() => {
    if (!search.trim()) return parts;
    const s = search.toLowerCase();
    return parts.filter(
      (p) =>
        p.part_no.includes(s) ||
        p.part_code.toLowerCase().includes(s) ||
        p.part_name.toLowerCase().includes(s)
    );
  }, [parts, search]);

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="px-6 py-5 border-b border-slate-200 bg-white">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-xl font-bold text-slate-800 flex items-center gap-2">
              <Layers className="w-6 h-6 text-blue-600" />
              BSR Parts Library
            </h1>
            <p className="text-sm text-slate-500 mt-0.5">31 canonical BSR work sections · Year availability matrix</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleClassify}
              disabled={classifying}
              className="flex items-center gap-1.5 px-3 py-2 bg-amber-500 text-white rounded-lg text-sm font-medium hover:bg-amber-600 disabled:opacity-50 transition-colors"
              title="Classify all unmapped BSR rate items into the 31 parts"
            >
              <ZapIcon className="w-4 h-4" />
              {classifying ? 'Classifying…' : 'Auto-Classify'}
            </button>
            <button
              onClick={load}
              className="p-2 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {classifyResult && (
          <div className="mb-3 p-2.5 bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm rounded-lg">
            {classifyResult}
          </div>
        )}

        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search parts…"
              className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-lg text-sm"
            />
          </div>
          <input
            type="text"
            value={district}
            onChange={(e) => setDistrict(e.target.value)}
            onBlur={load}
            placeholder="Filter by district"
            className="w-44 border border-slate-300 rounded-lg px-3 py-2 text-sm"
          />
        </div>
      </div>

      {/* Grid */}
      <div className="flex-1 overflow-auto p-6">
        {loading ? (
          <div className="text-center text-slate-400 py-20">Loading BSR Parts…</div>
        ) : (
          <table className="w-full border-collapse rounded-xl overflow-hidden shadow-sm">
            <thead>
              <tr className="bg-slate-800 text-white">
                <th className="px-4 py-3 text-left text-xs font-semibold">Part</th>
                <th className="px-4 py-3 text-left text-xs font-semibold">Code</th>
                <th className="px-4 py-3 text-left text-xs font-semibold">Name</th>
                <th className="px-4 py-3 text-right text-xs font-semibold">Total Items</th>
                {availableYears.map((yr) => (
                  <th key={yr} className="px-3 py-3 text-center text-xs font-semibold">{yr}</th>
                ))}
                <th className="px-4 py-3 text-center text-xs font-semibold">Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredParts.map((part, idx) => (
                <tr
                  key={part.id}
                  className={`border-b border-slate-100 hover:bg-blue-50 transition-colors ${
                    idx % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'
                  }`}
                >
                  <td className="px-4 py-3">
                    <span className="font-bold text-blue-600 text-sm">{part.part_no}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="font-mono text-xs bg-slate-100 text-slate-700 px-2 py-0.5 rounded">
                      {part.part_code}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-800 font-medium">{part.part_name}</td>
                  <td className="px-4 py-3 text-right tabular-nums text-sm font-semibold text-slate-700">
                    {part.total_items > 0 ? fmt0(part.total_items) : '—'}
                  </td>
                  {availableYears.map((yr) => {
                    const cnt = part.year_availability[yr];
                    return (
                      <td key={yr} className="px-3 py-3 text-center">
                        {cnt ? (
                          <span className="text-xs text-emerald-700 font-semibold" title={`${cnt} items`}>
                            ✓
                          </span>
                        ) : (
                          <span className="text-xs text-slate-300">–</span>
                        )}
                      </td>
                    );
                  })}
                  <td className="px-4 py-3 text-center">
                    <button
                      onClick={() => onSelectPart(part)}
                      disabled={part.total_items === 0}
                      className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white text-xs font-semibold rounded-lg hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors mx-auto"
                    >
                      Open <ChevronRight className="w-3 h-3" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

// ── Main Page ──────────────────────────────────────────────────────────────────

type View = 'library' | 'cross-year' | 'boq';

export const BSRPartsPage: React.FC = () => {
  const { user } = useAuth();
  const [view, setView] = useState<View>('library');
  const [selectedPart, setSelectedPart] = useState<CanonicalBSRPart | null>(null);
  const [openSelectionId, setOpenSelectionId] = useState<number | null>(null);
  const [currentSelection, setCurrentSelection] = useState<ProjectPartSelection | null>(null);
  const [loadingSelection, setLoadingSelection] = useState(false);

  const handleSelectPart = (part: CanonicalBSRPart) => {
    setSelectedPart(part);
    setView('cross-year');
  };

  const handleOpenBOQ = async (selectionId: number) => {
    setOpenSelectionId(selectionId);
    setLoadingSelection(true);
    setView('boq');
    try {
      const sel = await api.getPartSelection(selectionId);
      setCurrentSelection(sel);
    } finally {
      setLoadingSelection(false);
    }
  };

  const handleRefreshBOQ = async () => {
    if (!openSelectionId) return;
    const sel = await api.getPartSelection(openSelectionId);
    setCurrentSelection(sel);
  };

  if (view === 'library') {
    return (
      <div className="h-full bg-slate-50">
        <PartsLibrary onSelectPart={handleSelectPart} onOpenBOQ={handleOpenBOQ} />
      </div>
    );
  }

  if (view === 'cross-year' && selectedPart) {
    return (
      <div className="h-full bg-white">
        <CrossYearViewer
          part={selectedPart}
          onBack={() => setView('library')}
          onOpenBOQ={handleOpenBOQ}
        />
      </div>
    );
  }

  if (view === 'boq') {
    if (loadingSelection || !currentSelection) {
      return (
        <div className="h-full flex items-center justify-center text-slate-400">
          Loading Part BOQ…
        </div>
      );
    }
    return (
      <div className="h-full bg-white">
        <PartBOQWorkspace
          selection={currentSelection}
          userRole={user?.role || 'VIEWER'}
          onBack={() => {
            if (selectedPart) setView('cross-year');
            else setView('library');
          }}
          onRefresh={handleRefreshBOQ}
        />
      </div>
    );
  }

  return null;
};
