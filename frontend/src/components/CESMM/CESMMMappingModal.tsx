import React, { useState, useEffect } from 'react';
import { X, Layers, Plus, Trash2, Star, Check, Loader2 } from 'lucide-react';
import { api } from '../../api/client';
import { RateItem, CESMMSection, RateItemCESMM } from '../../types';

interface CESMMMappingModalProps {
  item: RateItem | null;
  isOpen?: boolean;
  onClose: () => void;
  onSaved?: (updatedMappings: RateItemCESMM[]) => void;
  onUpdated?: () => void;
}

export const CESMMMappingModal: React.FC<CESMMMappingModalProps> = ({
  item,
  isOpen = true,
  onClose,
  onSaved,
  onUpdated,
}) => {
  const [sections, setSections] = useState<CESMMSection[]>([]);
  const [selectedSectionId, setSelectedSectionId] = useState<number | ''>('');
  const [isPrimaryNew, setIsPrimaryNew] = useState<boolean>(false);
  const [mappings, setMappings] = useState<{ cesmm_section_id: number; is_primary: boolean }[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [saving, setSaving] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Load 31 CESMM sections and current item mappings
  useEffect(() => {
    if (!isOpen || !item) return;

    setErrorMsg(null);
    setSuccessMsg(null);
    setLoading(true);

    Promise.all([
      api.getCesmmSections(true),
      api.getItemCesmmMappings(item.id),
    ])
      .then(([secList, currentMappings]) => {
        setSections(secList);
        setMappings(
          currentMappings.map((m) => ({
            cesmm_section_id: m.cesmm_section_id,
            is_primary: m.is_primary,
          }))
        );
      })
      .catch((err) => {
        console.error('Failed to load CESMM data:', err);
        setErrorMsg('Failed to load CESMM sections or mappings.');
      })
      .finally(() => setLoading(false));
  }, [isOpen, item]);

  if (!isOpen || !item) return null;

  const handleAddSection = () => {
    if (!selectedSectionId) return;
    const secId = Number(selectedSectionId);
    if (mappings.some((m) => m.cesmm_section_id === secId)) {
      setErrorMsg('This CESMM section is already mapped to this item.');
      return;
    }

    const isFirst = mappings.length === 0;
    const makePrimary = isPrimaryNew || isFirst;

    const next = mappings.map((m) => (makePrimary ? { ...m, is_primary: false } : m));
    next.push({ cesmm_section_id: secId, is_primary: makePrimary });

    setMappings(next);
    setSelectedSectionId('');
    setIsPrimaryNew(false);
    setErrorMsg(null);
  };

  const handleRemoveMapping = (secId: number) => {
    const next = mappings.filter((m) => m.cesmm_section_id !== secId);
    // If we removed the primary, make the first remaining primary
    if (next.length > 0 && !next.some((m) => m.is_primary)) {
      next[0].is_primary = true;
    }
    setMappings(next);
  };

  const handleSetPrimary = (secId: number) => {
    const next = mappings.map((m) => ({
      ...m,
      is_primary: m.cesmm_section_id === secId,
    }));
    setMappings(next);
  };

  const handleSave = async () => {
    if (!item) return;
    try {
      setSaving(true);
      setErrorMsg(null);
      const res = await api.assignItemCesmmMappings(item.id, mappings);
      setSuccessMsg('CESMM-SL classifications successfully saved!');
      if (onSaved) {
        onSaved(res);
      }
      if (onUpdated) {
        onUpdated();
      }
      setTimeout(() => {
        onClose();
      }, 700);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to save CESMM mappings.');
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen || !item) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 overflow-y-auto">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="p-4 bg-slate-900 text-white flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-blue-600 rounded-lg text-white">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold">CESMM-SL Work Section Classification</h3>
              <p className="text-xs text-slate-400">
                Additional standard civil engineering measurement classification layer
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Item Summary Bar */}
        <div className="p-4 bg-slate-50 border-b border-slate-200 text-xs space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-mono font-bold text-blue-700 text-sm">
              {item.item_code || 'No Code'}
            </span>
            <div className="flex items-center gap-1.5">
              <span className="px-2 py-0.5 rounded font-bold bg-blue-100 text-blue-800 border border-blue-200">
                Rate Book: {item.rate_system}
              </span>
              {item.category_name && (
                <span className="px-2 py-0.5 rounded font-medium bg-slate-200 text-slate-700">
                  Trade: {item.category_name}
                </span>
              )}
            </div>
          </div>
          <p className="text-slate-800 font-medium leading-relaxed">{item.description}</p>
          <div className="flex items-center gap-4 text-slate-500 font-mono text-[11px]">
            <span>Unit: {item.unit || '-'}</span>
            <span>
              Rate: LKR {Number(item.rate || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </span>
            <span>Year: {item.year}</span>
          </div>
          <p className="text-[11px] text-amber-700 bg-amber-50 p-2 rounded border border-amber-200 leading-tight">
            ℹ️ <b>Rule:</b> Assigning CESMM sections does NOT change the item's original Rate Book or trade category.
          </p>
        </div>

        {/* Content Body */}
        <div className="p-5 space-y-4">
          {errorMsg && (
            <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-800">
              {errorMsg}
            </div>
          )}

          {successMsg && (
            <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 flex items-center gap-1.5">
              <Check className="w-4 h-4 text-emerald-600" />
              <span>{successMsg}</span>
            </div>
          )}

          {loading ? (
            <div className="py-8 flex items-center justify-center gap-2 text-slate-500 text-xs">
              <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
              <span>Loading CESMM sections...</span>
            </div>
          ) : (
            <>
              {/* Existing Mappings List */}
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                  Assigned CESMM Sections ({mappings.length})
                </label>
                {mappings.length === 0 ? (
                  <div className="p-4 rounded-xl border border-dashed border-slate-300 text-center text-xs text-slate-400">
                    No CESMM sections assigned yet. Select a section below to classify this item.
                  </div>
                ) : (
                  <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                    {mappings.map((m) => {
                      const sec = sections.find((s) => s.id === m.cesmm_section_id);
                      if (!sec) return null;
                      return (
                        <div
                          key={m.cesmm_section_id}
                          className={`flex items-center justify-between p-2.5 rounded-xl border transition-all text-xs ${
                            m.is_primary
                              ? 'bg-blue-50/70 border-blue-300'
                              : 'bg-white border-slate-200 hover:bg-slate-50'
                          }`}
                        >
                          <div className="flex items-center gap-2.5">
                            <span className="font-mono font-bold px-2 py-0.5 rounded bg-blue-100 text-blue-800 border border-blue-200">
                              CESMM {sec.section_no} · Sec {sec.section_code}
                            </span>
                            <div>
                              <div className="font-semibold text-slate-900">{sec.name}</div>
                              {m.is_primary && (
                                <span className="inline-flex items-center gap-0.5 text-[10px] font-bold text-blue-700">
                                  <Star className="w-3 h-3 fill-blue-600 text-blue-600" />
                                  Primary Classification
                                </span>
                              )}
                            </div>
                          </div>

                          <div className="flex items-center gap-1.5">
                            {!m.is_primary && (
                              <button
                                type="button"
                                onClick={() => handleSetPrimary(m.cesmm_section_id)}
                                className="px-2 py-1 rounded text-[11px] font-semibold text-slate-600 hover:text-blue-700 hover:bg-blue-100/60 border border-slate-200 transition-colors"
                              >
                                Make Primary
                              </button>
                            )}
                            <button
                              type="button"
                              onClick={() => handleRemoveMapping(m.cesmm_section_id)}
                              className="p-1.5 rounded text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
                              title="Remove CESMM mapping"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Add New Section Selector */}
              <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 space-y-2.5">
                <label className="block text-xs font-bold text-slate-700">
                  Assign Additional CESMM Section
                </label>
                <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
                  <select
                    value={selectedSectionId}
                    onChange={(e) => setSelectedSectionId(e.target.value ? Number(e.target.value) : '')}
                    className="flex-1 text-xs px-3 py-2 bg-white rounded-lg border border-slate-300 focus:outline-none focus:ring-1 focus:ring-blue-600"
                  >
                    <option value="">-- Choose from 31 CESMM Sections --</option>
                    {sections.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.section_no} - {s.name} (Section {s.section_code})
                      </option>
                    ))}
                  </select>

                  <button
                    type="button"
                    onClick={handleAddSection}
                    disabled={!selectedSectionId}
                    className="inline-flex items-center justify-center gap-1 px-3.5 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-xs disabled:opacity-50 transition-colors cursor-pointer"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Add</span>
                  </button>
                </div>

                <label className="flex items-center gap-2 text-xs text-slate-600 cursor-pointer pt-0.5">
                  <input
                    type="checkbox"
                    checked={isPrimaryNew}
                    onChange={(e) => setIsPrimaryNew(e.target.checked)}
                    className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 w-3.5 h-3.5"
                  />
                  <span>Mark as primary CESMM section for this item</span>
                </label>
              </div>
            </>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 bg-slate-50 border-t border-slate-200 flex items-center justify-end gap-2.5">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-white border border-slate-300 hover:bg-slate-100 text-slate-700 font-semibold text-xs transition-colors"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={saving || loading}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-xs transition-colors disabled:opacity-50 cursor-pointer"
          >
            {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
            <span>Save Classification</span>
          </button>
        </div>
      </div>
    </div>
  );
};
