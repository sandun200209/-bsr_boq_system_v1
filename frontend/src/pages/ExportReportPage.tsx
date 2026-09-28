import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  FileSpreadsheet,
  Download,
  Check,
  AlertTriangle,
  Layers,
  Settings2,
  Plus,
  Trash2,
  Edit3,
  Copy,
  ArrowUp,
  ArrowDown,
  Search,
  X,
  ChevronDown,
  ChevronRight,
  FolderPlus,
  Loader2,
  SlidersHorizontal,
  Calculator,
  BookOpen,
  Tag,
} from 'lucide-react';
import { api } from '../api/client';
import {
  MasterBOQ,
  MasterBOQItem,
  MasterBOQItemCreate,
  MasterBOQItemUpdate,
  RateItem,
  FilterOptions,
} from '../types';

interface ExportReportPageProps {
  navigationParams?: any;
  onNavigate?: (tab: string, params?: any) => void;
}

export const ExportReportPage: React.FC<ExportReportPageProps> = ({
  navigationParams,
  onNavigate,
}) => {
  // Master BOQ Workspaces
  const [boqs, setBoqs] = useState<MasterBOQ[]>([]);
  const [activeBoq, setActiveBoq] = useState<MasterBOQ | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [downloading, setDownloading] = useState<'excel' | 'pdf' | null>(null);

  // Grouping & Filtering Mode: 'flat' | 'cesmm' | 'rate_book'
  const [viewMode, setViewMode] = useState<'flat' | 'cesmm' | 'rate_book'>('flat');
  const [collapsedGroups, setCollapsedGroups] = useState<Record<string, boolean>>({});

  // Selection state for bulk operations
  const [selectedItemIds, setSelectedItemIds] = useState<Set<number>>(new Set());

  // In-line editing feedback
  const [toastMessage, setToastMessage] = useState<{ text: string; type: 'success' | 'info' | 'error' } | null>(null);

  // Modals
  const [showNewBOQModal, setShowNewBOQModal] = useState<boolean>(false);
  const [showAddCustomModal, setShowAddCustomModal] = useState<boolean>(false);
  const [showAddFromRatesModal, setShowAddFromRatesModal] = useState<boolean>(false);
  const [editingItem, setEditingItem] = useState<MasterBOQItem | null>(null);
  const [showSettingsDrawer, setShowSettingsDrawer] = useState<boolean>(false);

  // Form states for New BOQ
  const [newBOQName, setNewBOQName] = useState<string>('');
  const [newBOQContingency, setNewBOQContingency] = useState<number>(10);
  const [newBOQVAT, setNewBOQVAT] = useState<string>('Excluded');

  // Form states for Custom Item
  const [customItemNo, setCustomItemNo] = useState<string>('');
  const [customDesc, setCustomDesc] = useState<string>('');
  const [customUnit, setCustomUnit] = useState<string>('Item');
  const [customQty, setCustomQty] = useState<number>(1);
  const [customRate, setCustomRate] = useState<number>(0);
  const [customNotes, setCustomNotes] = useState<string>('');

  // Rate Search Modal state
  const [rateSearchQuery, setRateSearchQuery] = useState<string>('');
  const [rateSearchBook, setRateSearchBook] = useState<string>('');
  const [rateSearchCesmm, setRateSearchCesmm] = useState<string>('');
  const [rateSearchResults, setRateSearchResults] = useState<RateItem[]>([]);
  const [rateSearchLoading, setRateSearchLoading] = useState<boolean>(false);
  const [rateSearchSelectedIds, setRateSearchSelectedIds] = useState<Set<number>>(new Set());
  const [filterOpts, setFilterOpts] = useState<FilterOptions | null>(null);

  const showToast = (text: string, type: 'success' | 'info' | 'error' = 'success') => {
    setToastMessage({ text, type });
    setTimeout(() => setToastMessage(null), 4000);
  };

  // Load Active Master BOQ and list of all BOQs
  const fetchWorkspaces = useCallback(async (selectBoqId?: number) => {
    try {
      setLoading(true);
      const [boqList, active] = await Promise.all([
        api.listMasterBOQs(),
        api.getActiveMasterBOQ(),
      ]);
      setBoqs(boqList);

      if (selectBoqId) {
        const target = boqList.find((b) => b.id === selectBoqId) || active;
        setActiveBoq(target);
      } else {
        setActiveBoq(active);
      }
    } catch (err: any) {
      showToast(err.message || 'Failed to load Master BOQ', 'error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchWorkspaces();
  }, [fetchWorkspaces]);

  // Handle items passed via navigationParams (e.g. from Rate Search)
  useEffect(() => {
    if (activeBoq && navigationParams?.selectedIds && navigationParams.selectedIds.length > 0) {
      const addIncomingItems = async () => {
        try {
          const res = await api.addRatesToMasterBOQ(activeBoq.id, navigationParams.selectedIds);
          showToast(
            `Added ${res.added_count} items from search (${res.existing_count} already existed)`,
            'success'
          );
          // Refresh active BOQ
          const updated = await api.getMasterBOQ(activeBoq.id);
          setActiveBoq(updated);
        } catch (err: any) {
          showToast(`Error adding selected items: ${err.message}`, 'error');
        }
      };
      addIncomingItems();
    }
  }, [navigationParams?.selectedIds, activeBoq?.id]);

  // Calculate live totals
  const metrics = useMemo(() => {
    if (!activeBoq) {
      return {
        totalItems: 0,
        subtotal: 0,
        contingencyAmount: 0,
        grandTotal: 0,
        breakdown: { bsr: 0, hsr: 0, water: 0, custom: 0, other: 0 },
      };
    }
    const totalItems = activeBoq.items.length;
    const subtotal = activeBoq.items.reduce((sum, item) => sum + (item.amount || 0), 0);
    const contingencyAmount = subtotal * (activeBoq.contingency_rate || 0.10);
    const grandTotal = subtotal + contingencyAmount;

    const breakdown = { bsr: 0, hsr: 0, water: 0, custom: 0, other: 0 };
    activeBoq.items.forEach((item) => {
      const book = (item.source_rate_book || '').toUpperCase();
      if (item.is_custom || book === 'CUSTOM') {
        breakdown.custom++;
      } else if (book.includes('BSR')) {
        breakdown.bsr++;
      } else if (book.includes('HSR')) {
        breakdown.hsr++;
      } else if (book.includes('WATER')) {
        breakdown.water++;
      } else {
        breakdown.other++;
      }
    });

    return {
      totalItems,
      subtotal: Math.round(subtotal * 100) / 100,
      contingencyAmount: Math.round(contingencyAmount * 100) / 100,
      grandTotal: Math.round(grandTotal * 100) / 100,
      breakdown,
    };
  }, [activeBoq]);

  // Grouped items
  const groupedItems = useMemo(() => {
    if (!activeBoq) return {};
    const groups: Record<string, MasterBOQItem[]> = {};

    if (viewMode === 'cesmm') {
      activeBoq.items.forEach((it) => {
        const key = it.source_cesmm_section || 'Unclassified / General';
        if (!groups[key]) groups[key] = [];
        groups[key].push(it);
      });
    } else if (viewMode === 'rate_book') {
      activeBoq.items.forEach((it) => {
        const key = it.is_custom ? 'Custom Items' : (it.source_rate_book || 'Other Rate Book');
        if (!groups[key]) groups[key] = [];
        groups[key].push(it);
      });
    } else {
      // Flat list ordered by sort_order
      groups['All Items'] = [...activeBoq.items].sort((a, b) => a.sort_order - b.sort_order);
    }

    return groups;
  }, [activeBoq, viewMode]);

  // Switch Active BOQ Workspace
  const handleSwitchBOQ = async (boqId: number) => {
    try {
      setLoading(true);
      const boq = await api.getMasterBOQ(boqId);
      setActiveBoq(boq);
      setSelectedItemIds(new Set());
    } catch (err: any) {
      showToast(err.message || 'Failed to switch BOQ', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Create New BOQ Workspace
  const handleCreateNewBOQ = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newBOQName.trim()) return;
    try {
      setSaving(true);
      const created = await api.createMasterBOQ({
        name: newBOQName.trim(),
        contingency_rate: newBOQContingency / 100,
        vat_status: newBOQVAT,
      });
      setShowNewBOQModal(false);
      setNewBOQName('');
      showToast(`Master BOQ "${created.name}" created!`, 'success');
      await fetchWorkspaces(created.id);
    } catch (err: any) {
      showToast(err.message || 'Failed to create Master BOQ', 'error');
    } finally {
      setSaving(false);
    }
  };

  // Update BOQ Name / Settings
  const handleUpdateBOQSettings = async (updates: Partial<MasterBOQ>) => {
    if (!activeBoq) return;
    try {
      const updated = await api.updateMasterBOQ(activeBoq.id, {
        name: updates.name,
        status: updates.status,
        contingency_rate: updates.contingency_rate,
        vat_status: updates.vat_status,
        notes: updates.notes,
      });
      setActiveBoq(updated);
      showToast('Workspace settings updated', 'success');
    } catch (err: any) {
      showToast(err.message || 'Failed to update settings', 'error');
    }
  };

  // Delete Current BOQ
  const handleDeleteBOQ = async () => {
    if (!activeBoq) return;
    if (boqs.length <= 1) {
      alert('Cannot delete the only workspace. Create another workspace first.');
      return;
    }
    if (!window.confirm(`Are you sure you want to delete workspace "${activeBoq.name}"? Original rate items will NOT be affected.`)) {
      return;
    }
    try {
      setLoading(true);
      await api.deleteMasterBOQ(activeBoq.id);
      showToast('Workspace deleted', 'info');
      await fetchWorkspaces();
    } catch (err: any) {
      showToast(err.message || 'Failed to delete workspace', 'error');
      setLoading(false);
    }
  };

  // Inline Quantity or Rate Change with Auto-Save
  const handleInlineChange = async (itemId: number, field: 'quantity' | 'rate' | 'item_no', value: any) => {
    if (!activeBoq) return;

    // Optimistic UI update
    setActiveBoq((prev) => {
      if (!prev) return prev;
      const updatedItems = prev.items.map((it) => {
        if (it.id !== itemId) return it;
        const newQty = field === 'quantity' ? Math.max(0, parseFloat(value) || 0) : it.quantity;
        const newRate = field === 'rate' ? Math.max(0, parseFloat(value) || 0) : it.rate;
        const newItemNo = field === 'item_no' ? String(value) : it.item_no;
        const newAmount = Math.round(newQty * newRate * 100) / 100;
        return {
          ...it,
          quantity: newQty,
          rate: newRate,
          item_no: newItemNo,
          amount: newAmount,
          is_modified_rate: it.original_rate !== null && it.original_rate !== undefined && !it.is_custom
            ? Math.round(newRate * 100) !== Math.round(it.original_rate * 100)
            : false,
        };
      });
      return { ...prev, items: updatedItems };
    });

    try {
      const payload: MasterBOQItemUpdate = {};
      if (field === 'quantity') payload.quantity = Math.max(0, parseFloat(value) || 0);
      if (field === 'rate') payload.rate = Math.max(0, parseFloat(value) || 0);
      if (field === 'item_no') payload.item_no = String(value);

      await api.updateMasterBOQItem(activeBoq.id, itemId, payload);
    } catch (err: any) {
      showToast(`Failed to update item: ${err.message}`, 'error');
      // Re-fetch to sync
      const res = await api.getMasterBOQ(activeBoq.id);
      setActiveBoq(res);
    }
  };

  // Reorder Item Up or Down
  const handleMoveItem = async (itemId: number, direction: 'up' | 'down') => {
    if (!activeBoq) return;
    const sorted = [...activeBoq.items].sort((a, b) => a.sort_order - b.sort_order);
    const index = sorted.findIndex((it) => it.id === itemId);
    if (index === -1) return;

    const targetIndex = direction === 'up' ? index - 1 : index + 1;
    if (targetIndex < 0 || targetIndex >= sorted.length) return;

    // Swap sort orders
    const itemA = sorted[index];
    const itemB = sorted[targetIndex];
    const tempOrder = itemA.sort_order;
    itemA.sort_order = itemB.sort_order === tempOrder ? tempOrder + 1 : itemB.sort_order;
    itemB.sort_order = tempOrder;

    setActiveBoq({ ...activeBoq, items: sorted });

    try {
      await api.reorderMasterBOQItems(activeBoq.id, [
        { id: itemA.id, sort_order: itemA.sort_order },
        { id: itemB.id, sort_order: itemB.sort_order },
      ]);
    } catch (err: any) {
      showToast('Reorder failed', 'error');
    }
  };

  // Duplicate an Item
  const handleDuplicateItem = async (itemId: number) => {
    if (!activeBoq) return;
    try {
      setSaving(true);
      const cloned = await api.duplicateMasterBOQItem(activeBoq.id, itemId);
      setActiveBoq((prev) => prev ? { ...prev, items: [...prev.items, cloned] } : null);
      showToast('Item duplicated successfully', 'success');
    } catch (err: any) {
      showToast(err.message || 'Duplicate failed', 'error');
    } finally {
      setSaving(false);
    }
  };

  // Delete an Item
  const handleDeleteItem = async (itemId: number) => {
    if (!activeBoq) return;
    if (!window.confirm('Remove this item from the Master BOQ? (Original rate data is preserved)')) {
      return;
    }
    try {
      await api.deleteMasterBOQItem(activeBoq.id, itemId);
      setActiveBoq((prev) => prev ? { ...prev, items: prev.items.filter((it) => it.id !== itemId) } : null);
      setSelectedItemIds((prev) => {
        const next = new Set(prev);
        next.delete(itemId);
        return next;
      });
      showToast('Item removed from workspace', 'info');
    } catch (err: any) {
      showToast(err.message || 'Delete failed', 'error');
    }
  };

  // Bulk Delete Selected Items
  const handleBulkDelete = async () => {
    if (!activeBoq || selectedItemIds.size === 0) return;
    if (!window.confirm(`Delete ${selectedItemIds.size} selected items from this BOQ workspace?`)) {
      return;
    }
    try {
      setSaving(true);
      const res = await api.bulkDeleteMasterBOQItems(activeBoq.id, Array.from(selectedItemIds));
      setActiveBoq((prev) => prev ? { ...prev, items: prev.items.filter((it) => !selectedItemIds.has(it.id)) } : null);
      setSelectedItemIds(new Set());
      showToast(`Removed ${res.deleted_count} items from BOQ`, 'info');
    } catch (err: any) {
      showToast(err.message || 'Bulk delete failed', 'error');
    } finally {
      setSaving(false);
    }
  };

  // Add Custom Item Form Submission
  const handleAddCustomItem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeBoq || !customDesc.trim()) return;

    try {
      setSaving(true);
      const payload: MasterBOQItemCreate = {
        item_no: customItemNo.trim() || undefined,
        description: customDesc.trim(),
        unit: customUnit.trim() || 'Item',
        quantity: customQty,
        rate: customRate,
        notes: customNotes.trim() || undefined,
        is_custom: true,
      };

      const newItem = await api.addCustomItemToMasterBOQ(activeBoq.id, payload);
      setActiveBoq((prev) => prev ? { ...prev, items: [...prev.items, newItem] } : null);
      setShowAddCustomModal(false);
      setCustomItemNo('');
      setCustomDesc('');
      setCustomUnit('Item');
      setCustomQty(1);
      setCustomRate(0);
      setCustomNotes('');
      showToast('Custom item added to Master BOQ', 'success');
    } catch (err: any) {
      showToast(err.message || 'Failed to add custom item', 'error');
    } finally {
      setSaving(false);
    }
  };

  // Save Modal Edit Item
  const handleSaveEditItem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeBoq || !editingItem) return;

    try {
      setSaving(true);
      const payload: MasterBOQItemUpdate = {
        item_no: editingItem.item_no,
        description: editingItem.description,
        unit: editingItem.unit,
        quantity: editingItem.quantity,
        rate: editingItem.rate,
        notes: editingItem.notes,
      };

      const updated = await api.updateMasterBOQItem(activeBoq.id, editingItem.id, payload);
      setActiveBoq((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          items: prev.items.map((it) => (it.id === updated.id ? updated : it)),
        };
      });
      setEditingItem(null);
      showToast('Line item saved', 'success');
    } catch (err: any) {
      showToast(err.message || 'Failed to save item', 'error');
    } finally {
      setSaving(false);
    }
  };

  // Rate Search Modal query
  const performRateSearch = async () => {
    try {
      setRateSearchLoading(true);
      const res = await api.searchRates({
        q: rateSearchQuery || undefined,
        rate_system: rateSearchBook || undefined,
        cesmm_section_no: rateSearchCesmm || undefined,
        page: 1,
        page_size: 50,
      });
      setRateSearchResults(res.items);
    } catch (err: any) {
      console.error('Rate search error:', err);
    } finally {
      setRateSearchLoading(false);
    }
  };

  // Load filter options when opening modal
  useEffect(() => {
    if (showAddFromRatesModal) {
      api.getFilterOptions().then((opts) => setFilterOpts(opts)).catch(() => {});
      performRateSearch();
    }
  }, [showAddFromRatesModal]);

  const handleAddSelectedFromRates = async () => {
    if (!activeBoq || rateSearchSelectedIds.size === 0) return;
    try {
      setSaving(true);
      const res = await api.addRatesToMasterBOQ(activeBoq.id, Array.from(rateSearchSelectedIds));
      showToast(
        `Added ${res.added_count} items to Master BOQ (${res.existing_count} already existed)`,
        'success'
      );
      setShowAddFromRatesModal(false);
      setRateSearchSelectedIds(new Set());
      const updated = await api.getMasterBOQ(activeBoq.id);
      setActiveBoq(updated);
    } catch (err: any) {
      showToast(err.message || 'Failed to add items', 'error');
    } finally {
      setSaving(false);
    }
  };

  // Excel and PDF Export
  const handleExportExcel = async () => {
    if (!activeBoq) return;
    try {
      setDownloading('excel');
      await api.downloadMasterBOQExcel(activeBoq.id, `${activeBoq.name.replace(/\s+/g, '_')}.xlsx`);
      showToast('Excel (.xlsx) downloaded successfully', 'success');
    } catch (err: any) {
      showToast(err.message || 'Excel export failed', 'error');
    } finally {
      setDownloading(null);
    }
  };

  const handleExportPdf = async () => {
    if (!activeBoq) return;
    try {
      setDownloading('pdf');
      await api.downloadMasterBOQPdf(activeBoq.id, `${activeBoq.name.replace(/\s+/g, '_')}.pdf`);
      showToast('PDF report downloaded successfully', 'success');
    } catch (err: any) {
      showToast(err.message || 'PDF export failed', 'error');
    } finally {
      setDownloading(null);
    }
  };

  // Checkbox helpers
  const handleToggleSelectAll = () => {
    if (!activeBoq) return;
    if (selectedItemIds.size === activeBoq.items.length) {
      setSelectedItemIds(new Set());
    } else {
      setSelectedItemIds(new Set(activeBoq.items.map((it) => it.id)));
    }
  };

  const handleToggleItemSelect = (id: number) => {
    setSelectedItemIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleGroupCollapse = (groupName: string) => {
    setCollapsedGroups((prev) => ({ ...prev, [groupName]: !prev[groupName] }));
  };

  if (loading && !activeBoq) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <Loader2 className="w-8 h-8 text-teal-600 animate-spin" />
        <p className="text-slate-600 text-sm font-medium">Loading Master BOQ Workspace...</p>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* 1. WORKSPACE HEADER */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-5">
          <div className="space-y-1.5 flex-1 min-w-0">
            <div className="flex items-center gap-3">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-teal-50 text-teal-700 border border-teal-200">
                Master BOQ Workspace
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700">
                Status: <strong className="text-slate-900">{activeBoq?.status || 'ACTIVE'}</strong>
              </span>
              {activeBoq?.updated_at && (
                <span className="text-xs text-slate-400 hidden sm:inline">
                  Updated: {new Date(activeBoq.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              )}
            </div>

            {/* Editable Name */}
            <div className="flex items-center gap-3 pt-1">
              <input
                type="text"
                value={activeBoq?.name || ''}
                onChange={(e) => {
                  const val = e.target.value;
                  if (activeBoq) setActiveBoq({ ...activeBoq, name: val });
                }}
                onBlur={(e) => handleUpdateBOQSettings({ name: e.target.value })}
                className="text-2xl font-extrabold text-slate-900 bg-transparent hover:bg-slate-50 focus:bg-white focus:ring-2 focus:ring-teal-500 rounded-lg px-2 -ml-2 py-0.5 transition-all truncate border border-transparent hover:border-slate-300 focus:border-teal-500"
                title="Click to edit BOQ name"
              />
            </div>
            <p className="text-xs text-slate-500">
              Persistent QS estimating workspace. Edits to descriptions, quantities, and rates are isolated and do not mutate original rate books.
            </p>
          </div>

          {/* Workspace Switcher & Top Actions */}
          <div className="flex flex-wrap items-center gap-2.5">
            {/* BOQ Switcher Dropdown */}
            <div className="relative">
              <select
                value={activeBoq?.id || ''}
                onChange={(e) => handleSwitchBOQ(Number(e.target.value))}
                className="text-xs font-semibold rounded-xl border border-slate-300 bg-slate-50 hover:bg-white py-2 pl-3 pr-8 focus:outline-none focus:ring-2 focus:ring-teal-500 text-slate-800 cursor-pointer shadow-2xs"
              >
                {boqs.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name} ({b.total_items || (b.items ? b.items.length : 0)} items)
                  </option>
                ))}
              </select>
            </div>

            {/* New BOQ Button */}
            <button
              onClick={() => setShowNewBOQModal(true)}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition-colors shadow-2xs"
              title="Create a new independent Master BOQ"
            >
              <FolderPlus className="w-3.5 h-3.5 text-slate-600" />
              <span>New BOQ</span>
            </button>

            {/* Settings Drawer Toggle */}
            <button
              onClick={() => setShowSettingsDrawer(!showSettingsDrawer)}
              className={`inline-flex items-center gap-1.5 px-3 py-2 rounded-xl border text-xs font-semibold transition-colors shadow-2xs ${
                showSettingsDrawer
                  ? 'border-teal-500 bg-teal-50 text-teal-800'
                  : 'border-slate-300 bg-white hover:bg-slate-50 text-slate-700'
              }`}
            >
              <SlidersHorizontal className="w-3.5 h-3.5" />
              <span>Settings</span>
            </button>

            {/* Delete BOQ */}
            {boqs.length > 1 && (
              <button
                onClick={handleDeleteBOQ}
                className="p-2 rounded-xl hover:bg-rose-50 text-slate-400 hover:text-rose-600 transition-colors"
                title="Delete this BOQ workspace"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Expandable Settings Bar */}
        {showSettingsDrawer && (
          <div className="mt-5 pt-4 border-t border-slate-100 grid grid-cols-1 sm:grid-cols-3 gap-4 bg-slate-50/70 p-4 rounded-xl animate-in fade-in">
            <div>
              <label className="block text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-1">
                Contingency Rate (%)
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  min="0"
                  max="50"
                  step="0.5"
                  value={Math.round((activeBoq?.contingency_rate || 0.10) * 1000) / 10}
                  onChange={(e) => {
                    const val = parseFloat(e.target.value) || 0;
                    if (activeBoq) {
                      setActiveBoq({ ...activeBoq, contingency_rate: val / 100 });
                    }
                  }}
                  onBlur={(e) => {
                    const val = parseFloat(e.target.value) || 0;
                    handleUpdateBOQSettings({ contingency_rate: val / 100 });
                  }}
                  className="text-xs rounded-lg border border-slate-300 bg-white px-3 py-1.5 w-24 font-mono font-bold text-slate-800 focus:ring-2 focus:ring-teal-500"
                />
                <span className="text-xs text-slate-500">% on Subtotal</span>
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-1">
                VAT Status
              </label>
              <select
                value={activeBoq?.vat_status || 'Excluded'}
                onChange={(e) => {
                  const val = e.target.value;
                  if (activeBoq) setActiveBoq({ ...activeBoq, vat_status: val });
                  handleUpdateBOQSettings({ vat_status: val });
                }}
                className="text-xs rounded-lg border border-slate-300 bg-white px-3 py-1.5 w-full text-slate-800 font-medium focus:ring-2 focus:ring-teal-500"
              >
                <option value="Excluded">Excluded from Line Rates (Net)</option>
                <option value="Included">Included in Line Rates (Gross)</option>
                <option value="Exempt">VAT Exempt Project</option>
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-1">
                Workspace Status
              </label>
              <select
                value={activeBoq?.status || 'ACTIVE'}
                onChange={(e) => {
                  const val = e.target.value;
                  if (activeBoq) setActiveBoq({ ...activeBoq, status: val });
                  handleUpdateBOQSettings({ status: val });
                }}
                className="text-xs rounded-lg border border-slate-300 bg-white px-3 py-1.5 w-full text-slate-800 font-medium focus:ring-2 focus:ring-teal-500"
              >
                <option value="DRAFT">Draft Work In Progress</option>
                <option value="ACTIVE">Active Working BOQ</option>
                <option value="REVIEWED">QS Reviewed / Approved</option>
                <option value="FINALIZED">Finalized for Tender</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {/* 2. SUMMARY / METRICS CARDS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Total Items */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Total Line Items</p>
            <h3 className="text-2xl font-black text-slate-900 mt-1">{metrics.totalItems}</h3>
            <div className="flex items-center gap-1.5 mt-2 text-[11px] text-slate-600">
              <span className="font-semibold text-teal-700 bg-teal-50 px-1.5 py-0.5 rounded">
                {metrics.breakdown.bsr} BSR
              </span>
              <span className="font-semibold text-blue-700 bg-blue-50 px-1.5 py-0.5 rounded">
                {metrics.breakdown.hsr} HSR
              </span>
              <span className="font-semibold text-purple-700 bg-purple-50 px-1.5 py-0.5 rounded">
                {metrics.breakdown.custom} Custom
              </span>
            </div>
          </div>
          <div className="p-3 bg-teal-50 text-teal-700 rounded-xl">
            <Layers className="w-6 h-6" />
          </div>
        </div>

        {/* Card 2: Subtotal */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Subtotal</p>
            <h3 className="text-2xl font-black text-slate-900 mt-1">
              LKR {metrics.subtotal.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </h3>
            <p className="text-[11px] text-slate-400 mt-2">Sum of item amounts (Qty × Rate)</p>
          </div>
          <div className="p-3 bg-blue-50 text-blue-700 rounded-xl">
            <Calculator className="w-6 h-6" />
          </div>
        </div>

        {/* Card 3: Contingency */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">
              Contingency ({Math.round((activeBoq?.contingency_rate || 0.10) * 1000) / 10}%)
            </p>
            <h3 className="text-2xl font-black text-slate-900 mt-1">
              LKR {metrics.contingencyAmount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </h3>
            <p className="text-[11px] text-slate-400 mt-2">Provision for unforeseen works</p>
          </div>
          <div className="p-3 bg-amber-50 text-amber-700 rounded-xl">
            <Settings2 className="w-6 h-6" />
          </div>
        </div>

        {/* Card 4: Grand Total / Estimate */}
        <div className="bg-gradient-to-br from-slate-900 to-slate-800 text-white p-5 rounded-2xl shadow-xs flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-300 uppercase tracking-wider">Engineer's Estimate</p>
            <h3 className="text-2xl font-black text-teal-300 mt-1">
              LKR {metrics.grandTotal.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </h3>
            <p className="text-[11px] text-slate-400 mt-2">VAT: {activeBoq?.vat_status || 'Excluded'}</p>
          </div>
          <div className="p-3 bg-white/10 text-teal-400 rounded-xl">
            <FileSpreadsheet className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* 3. WORKSPACE ACTION BAR */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs flex flex-wrap items-center justify-between gap-3">
        {/* Left: View Mode Toggle & Add Item Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          {/* View Mode Pills */}
          <div className="flex items-center p-1 bg-slate-100 rounded-xl text-xs font-semibold">
            <button
              onClick={() => setViewMode('flat')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                viewMode === 'flat' ? 'bg-white text-slate-900 shadow-2xs font-bold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Flat List
            </button>
            <button
              onClick={() => setViewMode('cesmm')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                viewMode === 'cesmm' ? 'bg-white text-slate-900 shadow-2xs font-bold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Group by CESMM Section
            </button>
            <button
              onClick={() => setViewMode('rate_book')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                viewMode === 'rate_book' ? 'bg-white text-slate-900 shadow-2xs font-bold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Group by Rate Book
            </button>
          </div>

          {/* Add from Rate Search Modal button */}
          <button
            onClick={() => setShowAddFromRatesModal(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold shadow-xs transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add from Rate Search</span>
          </button>

          {/* Add Custom Item Modal button */}
          <button
            onClick={() => setShowAddCustomModal(true)}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Custom Item</span>
          </button>

          {/* Bulk Delete button (if items selected) */}
          {selectedItemIds.size > 0 && (
            <button
              onClick={handleBulkDelete}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-700 text-xs font-semibold transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Remove Selected ({selectedItemIds.size})</span>
            </button>
          )}
        </div>

        {/* Right: Export Downloads */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleExportExcel}
            disabled={downloading !== null || !activeBoq?.items.length}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white text-xs font-bold shadow-xs transition-colors cursor-pointer"
            title="Download formatted Master BOQ Excel file with formulas"
          >
            {downloading === 'excel' ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <FileSpreadsheet className="w-4 h-4" />
            )}
            <span>Export Excel (.xlsx)</span>
          </button>

          <button
            onClick={handleExportPdf}
            disabled={downloading !== null || !activeBoq?.items.length}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 disabled:opacity-50 text-white text-xs font-bold shadow-xs transition-colors cursor-pointer"
            title="Download print-ready QS Engineering Report PDF"
          >
            {downloading === 'pdf' ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Download className="w-4 h-4" />
            )}
            <span>Export PDF</span>
          </button>
        </div>
      </div>

      {/* 4. MAIN EDITABLE BOQ TABLE */}
      {activeBoq?.items.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center space-y-4">
          <div className="w-16 h-16 bg-teal-50 text-teal-600 rounded-2xl flex items-center justify-center mx-auto">
            <BookOpen className="w-8 h-8" />
          </div>
          <div className="max-w-md mx-auto space-y-1">
            <h3 className="text-base font-bold text-slate-800">Your Master BOQ Workspace is Empty</h3>
            <p className="text-xs text-slate-500">
              Export rate items directly from the <strong>Rate Search</strong> page, or use the buttons below to populate your BOQ schedule.
            </p>
          </div>
          <div className="flex items-center justify-center gap-3 pt-2">
            <button
              onClick={() => setShowAddFromRatesModal(true)}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold shadow-xs"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Search & Add Rates</span>
            </button>
            <button
              onClick={() => onNavigate && onNavigate('search')}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold"
            >
              <span>Go to Rate Search</span>
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {Object.entries(groupedItems).map(([groupTitle, items]) => {
            const isCollapsed = Boolean(collapsedGroups[groupTitle]);
            const groupSubtotal = items.reduce((sum, it) => sum + (it.amount || 0), 0);

            return (
              <div
                key={groupTitle}
                className="bg-white rounded-2xl border border-slate-200/90 shadow-xs overflow-hidden transition-all"
              >
                {/* Group Header (if not flat list) */}
                {viewMode !== 'flat' && (
                  <div
                    onClick={() => toggleGroupCollapse(groupTitle)}
                    className="p-3.5 px-5 bg-slate-50/90 border-b border-slate-200/70 flex items-center justify-between cursor-pointer hover:bg-slate-100/80 select-none transition-colors"
                  >
                    <div className="flex items-center gap-2.5">
                      {isCollapsed ? (
                        <ChevronRight className="w-4 h-4 text-slate-400" />
                      ) : (
                        <ChevronDown className="w-4 h-4 text-slate-400" />
                      )}
                      <h4 className="text-xs font-bold text-slate-800 tracking-wide">
                        {groupTitle}
                      </h4>
                      <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-slate-200 text-slate-700">
                        {items.length} {items.length === 1 ? 'item' : 'items'}
                      </span>
                    </div>

                    <div className="text-xs font-bold text-slate-800">
                      Subtotal: LKR {groupSubtotal.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                  </div>
                )}

                {/* Items Table */}
                {!isCollapsed && (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead>
                        <tr className="border-b border-slate-200 bg-slate-50/60 text-slate-600 font-semibold tracking-wider uppercase text-[10px]">
                          <th className="py-2.5 px-3 w-8 text-center">
                            <input
                              type="checkbox"
                              checked={activeBoq?.items.length ? selectedItemIds.size === activeBoq.items.length : false}
                              onChange={handleToggleSelectAll}
                              className="rounded border-slate-300 text-teal-600 focus:ring-teal-500 w-3.5 h-3.5 cursor-pointer"
                            />
                          </th>
                          {viewMode === 'flat' && <th className="py-2.5 px-2 w-12 text-center">Order</th>}
                          <th className="py-2.5 px-3 w-20">Item No</th>
                          <th className="py-2.5 px-3 min-w-[240px]">Description & Provenance</th>
                          <th className="py-2.5 px-3 w-44">CESMM Classification</th>
                          <th className="py-2.5 px-2 w-16 text-center">Unit</th>
                          <th className="py-2.5 px-2 w-24 text-right">Quantity</th>
                          <th className="py-2.5 px-2 w-32 text-right">Working Rate (LKR)</th>
                          <th className="py-2.5 px-3 w-32 text-right">Amount (LKR)</th>
                          <th className="py-2.5 px-3 w-24 text-center">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {items.map((item, idx) => {
                          const isSelected = selectedItemIds.has(item.id);
                          const isModified = item.is_modified_rate;

                          return (
                            <tr
                              key={item.id}
                              className={`hover:bg-slate-50/70 transition-colors ${
                                isSelected ? 'bg-teal-50/40' : ''
                              }`}
                            >
                              {/* Selection Checkbox */}
                              <td className="py-3 px-3 text-center">
                                <input
                                  type="checkbox"
                                  checked={isSelected}
                                  onChange={() => handleToggleItemSelect(item.id)}
                                  className="rounded border-slate-300 text-teal-600 focus:ring-teal-500 w-3.5 h-3.5 cursor-pointer"
                                />
                              </td>

                              {/* Reorder Buttons (Flat mode) */}
                              {viewMode === 'flat' && (
                                <td className="py-3 px-1 text-center whitespace-nowrap">
                                  <div className="flex items-center justify-center gap-0.5">
                                    <button
                                      disabled={idx === 0}
                                      onClick={() => handleMoveItem(item.id, 'up')}
                                      className="p-1 rounded hover:bg-slate-200 text-slate-400 hover:text-slate-700 disabled:opacity-20 cursor-pointer"
                                      title="Move up"
                                    >
                                      <ArrowUp className="w-3 h-3" />
                                    </button>
                                    <button
                                      disabled={idx === items.length - 1}
                                      onClick={() => handleMoveItem(item.id, 'down')}
                                      className="p-1 rounded hover:bg-slate-200 text-slate-400 hover:text-slate-700 disabled:opacity-20 cursor-pointer"
                                      title="Move down"
                                    >
                                      <ArrowDown className="w-3 h-3" />
                                    </button>
                                  </div>
                                </td>
                              )}

                              {/* Item No (Inline editable) */}
                              <td className="py-3 px-3 font-mono font-bold text-slate-800">
                                <input
                                  type="text"
                                  value={item.item_no || ''}
                                  onChange={(e) => handleInlineChange(item.id, 'item_no', e.target.value)}
                                  className="w-16 px-1.5 py-0.5 rounded border border-transparent hover:border-slate-300 focus:border-teal-500 focus:ring-1 focus:ring-teal-500 bg-transparent text-slate-800 font-mono text-xs"
                                />
                              </td>

                              {/* Description & Source Provenance */}
                              <td className="py-3 px-3">
                                <div className="space-y-1">
                                  <div className="font-medium text-slate-900 leading-snug">
                                    {item.description}
                                  </div>

                                  {/* Provenance Badge Line */}
                                  <div className="flex flex-wrap items-center gap-1.5 text-[10px] text-slate-500 font-medium">
                                    {item.is_custom ? (
                                      <span className="px-1.5 py-0.5 rounded bg-purple-50 text-purple-700 font-bold border border-purple-200">
                                        Custom Item
                                      </span>
                                    ) : (
                                      <>
                                        <span className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 font-semibold">
                                          {item.source_rate_book || 'Rate Book'}
                                        </span>
                                        {item.source_code && (
                                          <span className="font-mono text-slate-600 bg-slate-50 px-1 rounded border border-slate-200">
                                            {item.source_code}
                                          </span>
                                        )}
                                        {item.source_region && (
                                          <span>• {item.source_region}</span>
                                        )}
                                        {item.source_year && (
                                          <span>• {item.source_year}</span>
                                        )}
                                        {item.source_page && (
                                          <span>• P.{item.source_page}</span>
                                        )}
                                      </>
                                    )}
                                    {item.notes && (
                                      <span className="text-amber-700 italic">
                                        Note: {item.notes}
                                      </span>
                                    )}
                                  </div>
                                </div>
                              </td>

                              {/* CESMM Section */}
                              <td className="py-3 px-3">
                                {item.source_cesmm_section ? (
                                  <span className="inline-flex items-center gap-1 text-[11px] font-medium text-blue-800 bg-blue-50/90 px-2 py-0.5 rounded-md border border-blue-200/60 max-w-[190px] truncate" title={item.source_cesmm_section}>
                                    <Tag className="w-3 h-3 shrink-0 text-blue-500" />
                                    <span className="truncate">{item.source_cesmm_section}</span>
                                  </span>
                                ) : (
                                  <span className="text-slate-400 italic text-[11px]">—</span>
                                )}
                              </td>

                              {/* Unit */}
                              <td className="py-3 px-2 text-center font-medium text-slate-700">
                                <span className="bg-slate-100 px-1.5 py-0.5 rounded font-mono text-[11px]">
                                  {item.unit || 'Item'}
                                </span>
                              </td>

                              {/* Quantity (Inline editable input) */}
                              <td className="py-3 px-2 text-right">
                                <input
                                  type="number"
                                  min="0"
                                  step="any"
                                  value={item.quantity}
                                  onChange={(e) => handleInlineChange(item.id, 'quantity', e.target.value)}
                                  className="w-20 px-2 py-1 rounded border border-slate-200 hover:border-slate-400 focus:border-teal-500 focus:ring-1 focus:ring-teal-500 text-right font-mono text-xs font-semibold text-slate-900 bg-white shadow-2xs"
                                  placeholder="0.00"
                                />
                              </td>

                              {/* Working Rate (Inline editable input) */}
                              <td className="py-3 px-2 text-right">
                                <div className="space-y-0.5">
                                  <input
                                    type="number"
                                    min="0"
                                    step="any"
                                    value={item.rate}
                                    onChange={(e) => handleInlineChange(item.id, 'rate', e.target.value)}
                                    className={`w-28 px-2 py-1 rounded border text-right font-mono text-xs font-semibold shadow-2xs ${
                                      isModified
                                        ? 'border-amber-400 bg-amber-50/50 text-amber-950 focus:border-amber-600 focus:ring-amber-500'
                                        : 'border-slate-200 hover:border-slate-400 focus:border-teal-500 focus:ring-1 focus:ring-teal-500 bg-white text-slate-900'
                                    }`}
                                    placeholder="0.00"
                                  />
                                  {isModified && item.original_rate !== null && item.original_rate !== undefined && (
                                    <div className="text-[10px] text-amber-700 font-semibold">
                                      Orig: LKR {item.original_rate.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                                    </div>
                                  )}
                                </div>
                              </td>

                              {/* Working Amount (Calculated) */}
                              <td className="py-3 px-3 text-right font-mono font-bold text-slate-900">
                                LKR {(item.amount || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                              </td>

                              {/* Actions */}
                              <td className="py-3 px-3 text-center">
                                <div className="flex items-center justify-center gap-1">
                                  <button
                                    onClick={() => setEditingItem(item)}
                                    className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-500 hover:text-slate-800 transition-colors"
                                    title="Edit description / full details"
                                  >
                                    <Edit3 className="w-3.5 h-3.5" />
                                  </button>

                                  <button
                                    onClick={() => handleDuplicateItem(item.id)}
                                    className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-500 hover:text-slate-800 transition-colors"
                                    title="Duplicate item"
                                  >
                                    <Copy className="w-3.5 h-3.5" />
                                  </button>

                                  <button
                                    onClick={() => handleDeleteItem(item.id)}
                                    className="p-1.5 rounded-lg hover:bg-rose-50 text-slate-400 hover:text-rose-600 transition-colors"
                                    title="Delete line item"
                                  >
                                    <Trash2 className="w-3.5 h-3.5" />
                                  </button>
                                </div>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* 5. MODAL: CREATE NEW MASTER BOQ */}
      {showNewBOQModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-5 animate-in fade-in">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <FolderPlus className="w-5 h-5 text-teal-600" />
                <h3 className="font-bold text-base text-slate-900">Create New Master BOQ</h3>
              </div>
              <button
                onClick={() => setShowNewBOQModal(false)}
                className="text-slate-400 hover:text-slate-600 p-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateNewBOQ} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  BOQ / Project Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Matara Hospital Ward Extension BOQ"
                  value={newBOQName}
                  onChange={(e) => setNewBOQName(e.target.value)}
                  className="w-full text-xs rounded-xl border border-slate-300 px-3.5 py-2.5 focus:outline-none focus:ring-2 focus:ring-teal-500 font-medium text-slate-900"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Contingency Rate (%)
                </label>
                <input
                  type="number"
                  min="0"
                  max="50"
                  step="0.5"
                  value={newBOQContingency}
                  onChange={(e) => setNewBOQContingency(parseFloat(e.target.value) || 0)}
                  className="w-full text-xs rounded-xl border border-slate-300 px-3.5 py-2.5 focus:outline-none focus:ring-2 focus:ring-teal-500 font-mono text-slate-900"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  VAT Treatment
                </label>
                <select
                  value={newBOQVAT}
                  onChange={(e) => setNewBOQVAT(e.target.value)}
                  className="w-full text-xs rounded-xl border border-slate-300 px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-teal-500 text-slate-900"
                >
                  <option value="Excluded">Excluded from Line Rates (Net Rates)</option>
                  <option value="Included">Included in Line Rates (Gross Rates)</option>
                  <option value="Exempt">VAT Exempt</option>
                </select>
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowNewBOQModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving || !newBOQName.trim()}
                  className="px-5 py-2 rounded-xl text-xs font-bold bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white shadow-xs"
                >
                  {saving ? 'Creating...' : 'Create Workspace'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 6. MODAL: ADD CUSTOM ITEM */}
      {showAddCustomModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-5 animate-in fade-in">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Plus className="w-5 h-5 text-teal-600" />
                <h3 className="font-bold text-base text-slate-900">Add Custom Item to BOQ</h3>
              </div>
              <button
                onClick={() => setShowAddCustomModal(false)}
                className="text-slate-400 hover:text-slate-600 p-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleAddCustomItem} className="space-y-4">
              <div className="grid grid-cols-3 gap-3">
                <div className="col-span-1">
                  <label className="block text-[11px] font-bold text-slate-600 uppercase mb-1">Item No</label>
                  <input
                    type="text"
                    placeholder="e.g. PS-01"
                    value={customItemNo}
                    onChange={(e) => setCustomItemNo(e.target.value)}
                    className="w-full text-xs rounded-xl border border-slate-300 px-3 py-2 font-mono text-slate-800"
                  />
                </div>
                <div className="col-span-2">
                  <label className="block text-[11px] font-bold text-slate-600 uppercase mb-1">Unit</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Item, m, m2, m3, kg, No"
                    value={customUnit}
                    onChange={(e) => setCustomUnit(e.target.value)}
                    className="w-full text-xs rounded-xl border border-slate-300 px-3 py-2 text-slate-800"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-bold text-slate-600 uppercase mb-1">Description *</label>
                <textarea
                  required
                  rows={3}
                  placeholder="Provide detailed description of the custom scope / item..."
                  value={customDesc}
                  onChange={(e) => setCustomDesc(e.target.value)}
                  className="w-full text-xs rounded-xl border border-slate-300 p-3 text-slate-800"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-bold text-slate-600 uppercase mb-1">Quantity</label>
                  <input
                    type="number"
                    min="0"
                    step="any"
                    value={customQty}
                    onChange={(e) => setCustomQty(parseFloat(e.target.value) || 0)}
                    className="w-full text-xs rounded-xl border border-slate-300 px-3 py-2 font-mono text-right"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-bold text-slate-600 uppercase mb-1">Rate (LKR)</label>
                  <input
                    type="number"
                    min="0"
                    step="any"
                    value={customRate}
                    onChange={(e) => setCustomRate(parseFloat(e.target.value) || 0)}
                    className="w-full text-xs rounded-xl border border-slate-300 px-3 py-2 font-mono text-right"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-bold text-slate-600 uppercase mb-1">Notes / Remarks</label>
                <input
                  type="text"
                  placeholder="Optional notes or supplier references"
                  value={customNotes}
                  onChange={(e) => setCustomNotes(e.target.value)}
                  className="w-full text-xs rounded-xl border border-slate-300 px-3 py-2 text-slate-800"
                />
              </div>

              <div className="flex items-center justify-between pt-3 border-t border-slate-100">
                <div className="text-xs font-bold text-slate-700">
                  Total: LKR {(customQty * customRate).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setShowAddCustomModal(false)}
                    className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={saving || !customDesc.trim()}
                    className="px-5 py-2 rounded-xl text-xs font-bold bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white shadow-xs"
                  >
                    {saving ? 'Adding...' : 'Add to BOQ'}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 7. MODAL: EDIT LINE ITEM DETAILS */}
      {editingItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-2xl space-y-5 animate-in fade-in">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Edit3 className="w-5 h-5 text-teal-600" />
                <h3 className="font-bold text-base text-slate-900">Edit BOQ Line Item</h3>
              </div>
              <button
                onClick={() => setEditingItem(null)}
                className="text-slate-400 hover:text-slate-600 p-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleSaveEditItem} className="space-y-4">
              {/* Read-only Source Provenance */}
              {!editingItem.is_custom && (
                <div className="bg-slate-50 p-3 rounded-xl border border-slate-200/80 text-[11px] space-y-1">
                  <div className="font-bold text-slate-700 uppercase tracking-wider">Source Provenance (Original Data)</div>
                  <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-slate-600">
                    <div>Rate Book: <strong className="text-slate-800">{editingItem.source_rate_book || 'N/A'}</strong></div>
                    <div>Source Code: <strong className="text-slate-800 font-mono">{editingItem.source_code || 'N/A'}</strong></div>
                    <div>Region: <strong className="text-slate-800">{editingItem.source_region || 'N/A'}</strong></div>
                    <div>Year / Rev: <strong className="text-slate-800">{editingItem.source_year} ({editingItem.source_revision || '—'})</strong></div>
                    <div>Original Base Rate: <strong className="text-slate-800 font-mono">LKR {(editingItem.original_rate || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}</strong></div>
                    <div>Source Page: <strong className="text-slate-800">{editingItem.source_page ? `Page ${editingItem.source_page}` : '—'}</strong></div>
                  </div>
                </div>
              )}

              <div className="grid grid-cols-3 gap-3">
                <div className="col-span-1">
                  <label className="block text-[11px] font-bold text-slate-600 uppercase mb-1">Item No</label>
                  <input
                    type="text"
                    value={editingItem.item_no || ''}
                    onChange={(e) => setEditingItem({ ...editingItem, item_no: e.target.value })}
                    className="w-full text-xs rounded-xl border border-slate-300 px-3 py-2 font-mono text-slate-800"
                  />
                </div>
                <div className="col-span-2">
                  <label className="block text-[11px] font-bold text-slate-600 uppercase mb-1">Unit</label>
                  <input
                    type="text"
                    value={editingItem.unit || ''}
                    onChange={(e) => setEditingItem({ ...editingItem, unit: e.target.value })}
                    className="w-full text-xs rounded-xl border border-slate-300 px-3 py-2 text-slate-800"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-bold text-slate-600 uppercase mb-1">Working Description</label>
                <textarea
                  rows={4}
                  value={editingItem.description}
                  onChange={(e) => setEditingItem({ ...editingItem, description: e.target.value })}
                  className="w-full text-xs rounded-xl border border-slate-300 p-3 text-slate-800"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-bold text-slate-600 uppercase mb-1">Working Quantity</label>
                  <input
                    type="number"
                    min="0"
                    step="any"
                    value={editingItem.quantity}
                    onChange={(e) => {
                      const qty = Math.max(0, parseFloat(e.target.value) || 0);
                      setEditingItem({
                        ...editingItem,
                        quantity: qty,
                        amount: Math.round(qty * editingItem.rate * 100) / 100,
                      });
                    }}
                    className="w-full text-xs rounded-xl border border-slate-300 px-3 py-2 font-mono text-right font-bold text-slate-900"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-bold text-slate-600 uppercase mb-1">Working Rate (LKR)</label>
                  <input
                    type="number"
                    min="0"
                    step="any"
                    value={editingItem.rate}
                    onChange={(e) => {
                      const r = Math.max(0, parseFloat(e.target.value) || 0);
                      setEditingItem({
                        ...editingItem,
                        rate: r,
                        amount: Math.round(editingItem.quantity * r * 100) / 100,
                      });
                    }}
                    className="w-full text-xs rounded-xl border border-slate-300 px-3 py-2 font-mono text-right font-bold text-slate-900"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-bold text-slate-600 uppercase mb-1">Working Remarks / Notes</label>
                <input
                  type="text"
                  value={editingItem.notes || ''}
                  onChange={(e) => setEditingItem({ ...editingItem, notes: e.target.value })}
                  className="w-full text-xs rounded-xl border border-slate-300 px-3 py-2 text-slate-800"
                  placeholder="e.g. Approved variation / special supplier rate"
                />
              </div>

              <div className="flex items-center justify-between pt-3 border-t border-slate-100">
                <div className="text-xs font-bold text-slate-700">
                  Working Amount: LKR {(editingItem.quantity * editingItem.rate).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setEditingItem(null)}
                    className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={saving}
                    className="px-5 py-2 rounded-xl text-xs font-bold bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white shadow-xs"
                  >
                    {saving ? 'Saving...' : 'Save Item'}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 8. MODAL: ADD FROM RATE SEARCH */}
      {showAddFromRatesModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl max-w-4xl w-full p-6 shadow-2xl space-y-4 max-h-[90vh] flex flex-col animate-in fade-in">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Search className="w-5 h-5 text-teal-600" />
                <h3 className="font-bold text-base text-slate-900">Add Rate Items to Master BOQ</h3>
              </div>
              <button
                onClick={() => setShowAddFromRatesModal(false)}
                className="text-slate-400 hover:text-slate-600 p-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Filter controls */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 bg-slate-50 p-3 rounded-xl">
              <div>
                <input
                  type="text"
                  placeholder="Search code or description..."
                  value={rateSearchQuery}
                  onChange={(e) => setRateSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && performRateSearch()}
                  className="w-full text-xs rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-slate-800"
                />
              </div>

              <div>
                <select
                  value={rateSearchBook}
                  onChange={(e) => {
                    setRateSearchBook(e.target.value);
                  }}
                  className="w-full text-xs rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-slate-800"
                >
                  <option value="">All Rate Books</option>
                  {filterOpts?.rate_systems?.map((book) => (
                    <option key={book} value={book}>{book}</option>
                  ))}
                </select>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={performRateSearch}
                  className="px-4 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs transition-colors flex items-center gap-1.5"
                >
                  <Search className="w-3.5 h-3.5" />
                  <span>Search</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setRateSearchQuery('');
                    setRateSearchBook('');
                    setRateSearchCesmm('');
                    performRateSearch();
                  }}
                  className="text-xs text-slate-500 hover:text-slate-800 font-medium"
                >
                  Reset
                </button>
              </div>
            </div>

            {/* Search Results Table */}
            <div className="flex-1 overflow-y-auto border border-slate-200 rounded-xl min-h-[300px]">
              {rateSearchLoading ? (
                <div className="flex items-center justify-center p-12 text-slate-500 gap-2">
                  <Loader2 className="w-5 h-5 animate-spin text-teal-600" />
                  <span className="text-xs">Searching rate items...</span>
                </div>
              ) : rateSearchResults.length === 0 ? (
                <div className="p-12 text-center text-xs text-slate-400">
                  No rate items found. Try adjusting your search query.
                </div>
              ) : (
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-slate-50 sticky top-0 border-b border-slate-200 text-slate-600 font-semibold uppercase text-[10px]">
                    <tr>
                      <th className="py-2 px-3 w-8 text-center">
                        <input
                          type="checkbox"
                          checked={rateSearchSelectedIds.size === rateSearchResults.length && rateSearchResults.length > 0}
                          onChange={() => {
                            if (rateSearchSelectedIds.size === rateSearchResults.length) {
                              setRateSearchSelectedIds(new Set());
                            } else {
                              setRateSearchSelectedIds(new Set(rateSearchResults.map((r) => r.id)));
                            }
                          }}
                          className="rounded border-slate-300 text-teal-600 focus:ring-teal-500 w-3.5 h-3.5 cursor-pointer"
                        />
                      </th>
                      <th className="py-2 px-2 w-20">Book</th>
                      <th className="py-2 px-2 w-20">Code</th>
                      <th className="py-2 px-3">Description</th>
                      <th className="py-2 px-2 w-16 text-center">Unit</th>
                      <th className="py-2 px-3 w-28 text-right">Rate (LKR)</th>
                      <th className="py-2 px-3 w-28">Region</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {rateSearchResults.map((it) => {
                      const isChecked = rateSearchSelectedIds.has(it.id);
                      return (
                        <tr
                          key={it.id}
                          onClick={() => {
                            setRateSearchSelectedIds((prev) => {
                              const next = new Set(prev);
                              if (next.has(it.id)) next.delete(it.id);
                              else next.add(it.id);
                              return next;
                            });
                          }}
                          className={`hover:bg-slate-50 cursor-pointer ${
                            isChecked ? 'bg-teal-50/50' : ''
                          }`}
                        >
                          <td className="py-2 px-3 text-center" onClick={(e) => e.stopPropagation()}>
                            <input
                              type="checkbox"
                              checked={isChecked}
                              onChange={() => {
                                setRateSearchSelectedIds((prev) => {
                                  const next = new Set(prev);
                                  if (next.has(it.id)) next.delete(it.id);
                                  else next.add(it.id);
                                  return next;
                                });
                              }}
                              className="rounded border-slate-300 text-teal-600 focus:ring-teal-500 w-3.5 h-3.5 cursor-pointer"
                            />
                          </td>
                          <td className="py-2 px-2 font-semibold text-slate-700">{it.rate_system}</td>
                          <td className="py-2 px-2 font-mono font-bold text-slate-900">{it.item_code}</td>
                          <td className="py-2 px-3 text-slate-800 line-clamp-2">{it.description}</td>
                          <td className="py-2 px-2 text-center text-slate-600 font-mono">{it.unit || 'Item'}</td>
                          <td className="py-2 px-3 text-right font-mono font-bold text-slate-900">
                            {(it.rate || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                          </td>
                          <td className="py-2 px-3 text-slate-500 text-[11px]">
                            {it.district ? `${it.district}, ${it.year}` : it.year}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              )}
            </div>

            {/* Footer with selection summary */}
            <div className="flex items-center justify-between pt-2 border-t border-slate-100">
              <span className="text-xs font-semibold text-slate-600">
                {rateSearchSelectedIds.size} items selected
              </span>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setShowAddFromRatesModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  disabled={saving || rateSearchSelectedIds.size === 0}
                  onClick={handleAddSelectedFromRates}
                  className="px-5 py-2 rounded-xl text-xs font-bold bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white shadow-xs"
                >
                  {saving ? 'Adding...' : `Add Selected (${rateSearchSelectedIds.size}) to BOQ`}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Floating Toast Notification */}
      {toastMessage && (
        <div
          className={`fixed bottom-6 right-6 z-50 px-4 py-3 rounded-xl shadow-2xl flex items-center gap-3 border animate-in fade-in slide-in-from-bottom-4 ${
            toastMessage.type === 'error'
              ? 'bg-rose-900 text-white border-rose-700'
              : toastMessage.type === 'info'
              ? 'bg-slate-900 text-white border-slate-700'
              : 'bg-teal-950 text-white border-teal-700'
          }`}
        >
          {toastMessage.type === 'error' ? (
            <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
          ) : (
            <Check className="w-4 h-4 text-teal-400 shrink-0" />
          )}
          <span className="text-xs font-medium">{toastMessage.text}</span>
          <button
            onClick={() => setToastMessage(null)}
            className="text-slate-400 hover:text-white p-1 rounded"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}
    </div>
  );
};
