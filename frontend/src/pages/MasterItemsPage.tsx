import React, { useState, useEffect } from 'react';
import {
  Plus,
  Link,
  Unlink,
  Check,
  Search,
  Sparkles,
} from 'lucide-react';
import { api } from '../api/client';
import { MasterItem, MasterSuggestion } from '../types';
import { SECTORS, RATE_SYSTEMS, SECTOR_RATE_SYSTEM_MAP, SECTOR_BADGE_CLASSES } from '../constants/sriLanka';

export const MasterItemsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'registry' | 'suggestions'>('registry');
  const [masterItems, setMasterItems] = useState<MasterItem[]>([]);
  const [suggestions, setSuggestions] = useState<MasterSuggestion[]>([]);
  const [selectedMaster, setSelectedMaster] = useState<MasterItem | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [sectorFilter, setSectorFilter] = useState<string>('');

  // Create Modal State
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [newCode, setNewCode] = useState<string>('');
  const [newDesc, setNewDesc] = useState<string>('');
  const [newUnit, setNewUnit] = useState<string>('m³');
  const [newCategory, setNewCategory] = useState<string>('Brick Layer');
  const [newSector, setNewSector] = useState<string>('Building Works');
  const [newRateSystem, setNewRateSystem] = useState<string>('BSR');
  const [newNotes, setNewNotes] = useState<string>('');

  const loadData = async () => {
    try {
      setLoading(true);
      const [masters, suggs] = await Promise.all([
        api.getMasterItems({
          q: searchQuery || undefined,
          sector: sectorFilter || undefined,
        }),
        api.getMasterSuggestions(25),
      ]);
      setMasterItems(masters);
      setSuggestions(suggs);
      if (masters.length > 0 && !selectedMaster) {
        // Load details of first master
        const detail = await api.getMasterItem(masters[0].id);
        setSelectedMaster(detail);
      }
    } catch (err) {
      console.error('Failed to load master items:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [searchQuery, sectorFilter]);

  const selectMasterItem = async (id: number) => {
    try {
      const detail = await api.getMasterItem(id);
      setSelectedMaster(detail);
    } catch (err) {
      console.error(err);
    }
  };

  const handleCreateMaster = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const created = await api.createMasterItem({
        master_code: newCode,
        canonical_description: newDesc,
        canonical_unit: newUnit,
        category: newCategory,
        sector: newSector,
        rate_system: newRateSystem,
        notes: newNotes,
      });
      setShowCreateModal(false);
      setNewCode('');
      setNewDesc('');
      loadData();
      selectMasterItem(created.id);
    } catch (err: any) {
      alert(err.message || 'Failed to create master item');
    }
  };

  const handleApproveSuggestion = async (suggestion: MasterSuggestion) => {
    try {
      await api.mapRateToMaster(suggestion.suggested_master_id, suggestion.rate_item.id);
      setSuggestions((prev) =>
        prev.filter((s) => s.rate_item.id !== suggestion.rate_item.id)
      );
      if (selectedMaster && selectedMaster.id === suggestion.suggested_master_id) {
        selectMasterItem(selectedMaster.id);
      }
      alert(`Mapped ${suggestion.rate_item.item_code} to Master ${suggestion.master_code}`);
    } catch (err: any) {
      alert(err.message || 'Failed to map suggestion');
    }
  };

  const handleUnmap = async (rateItemId: number) => {
    try {
      await api.unmapRateFromMaster(rateItemId);
      if (selectedMaster) {
        selectMasterItem(selectedMaster.id);
      }
    } catch (err: any) {
      alert(err.message || 'Failed to unmap item');
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Master Item Registry</h2>
          <p className="text-xs text-slate-500 mt-1">
            Map differing provincial codes (e.g. Southern BK01, Uva D-15, Central BR-04) to canonical Master Items for cross-island rate intelligence.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex bg-slate-200/80 p-1 rounded-xl text-xs font-semibold">
            <button
              onClick={() => setActiveTab('registry')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                activeTab === 'registry' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600'
              }`}
            >
              Canonical Registry
            </button>
            <button
              onClick={() => setActiveTab('suggestions')}
              className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
                activeTab === 'suggestions' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5 text-amber-500" />
              <span>Smart Suggestions ({suggestions.length})</span>
            </button>
          </div>

          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs rounded-xl shadow-xs"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Master Item</span>
          </button>
        </div>
      </div>

      {activeTab === 'registry' ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Left Master Items List (1 col) */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-4 flex flex-col h-[650px]">
            <div className="flex gap-2 mb-3">
              <select
                value={sectorFilter}
                onChange={(e) => setSectorFilter(e.target.value)}
                className="w-1/3 py-1.5 px-2 text-xs rounded-lg border border-slate-300 bg-white focus:ring-2 focus:ring-blue-600 focus:outline-none font-medium"
              >
                <option value="">All Sectors</option>
                {SECTORS.map((s) => (
                  <option key={s} value={s}>{s.split(' ')[0]}</option>
                ))}
              </select>
              <div className="relative flex-1">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2" />
                <input
                  type="text"
                  placeholder="Search master items..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-600 focus:outline-none"
                />
              </div>
            </div>

            <div className="flex-1 overflow-y-auto space-y-2 pr-1">
              {loading ? (
                <div className="text-center py-10 text-slate-400 text-xs">
                  Loading master items...
                </div>
              ) : masterItems.length === 0 ? (
                <div className="text-center py-10 text-slate-400 text-xs">
                  No master items found. Create your first master item to begin cross-mapping.
                </div>
              ) : (
                masterItems.map((master) => {
                  const isSelected = selectedMaster?.id === master.id;
                  return (
                    <div
                      key={master.id}
                      onClick={() => selectMasterItem(master.id)}
                      className={`p-3 rounded-xl border text-xs cursor-pointer transition-all ${
                        isSelected
                          ? 'bg-blue-50/80 border-blue-500 shadow-xs'
                          : 'bg-white border-slate-200 hover:border-slate-300'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-1.5">
                          {master.sector && (
                            <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold border ${SECTOR_BADGE_CLASSES[master.sector] || 'bg-slate-100 text-slate-700'}`}>
                              {master.rate_system || master.sector.split(' ')[0]}
                            </span>
                          )}
                          <span className="font-mono font-bold text-blue-700">{master.master_code}</span>
                        </div>
                        <span className="px-1.5 py-0.5 bg-slate-100 text-slate-600 rounded text-[10px] font-semibold">
                          {master.mapped_count} mapped
                        </span>
                      </div>
                      <div className="font-semibold text-slate-800 mt-1 line-clamp-2">
                        {master.canonical_description}
                      </div>
                      <div className="text-[11px] text-slate-400 mt-1 flex justify-between">
                        <span>{master.category || 'General'}</span>
                        <span className="font-mono">{master.canonical_unit}</span>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* Right Mapped Provincial Items View (2 cols) */}
          <div className="md:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-xs p-6 flex flex-col h-[650px]">
            {selectedMaster ? (
              <div className="flex flex-col h-full space-y-5">
                {/* Master Details Header */}
                <div className="border-b border-slate-100 pb-4">
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-lg text-blue-700">
                      {selectedMaster.master_code}
                    </span>
                    <span className="px-2.5 py-1 bg-blue-50 text-blue-700 text-xs font-bold rounded-lg">
                      {selectedMaster.canonical_unit}
                    </span>
                  </div>
                  <h3 className="text-sm font-bold text-slate-900 mt-1">
                    {selectedMaster.canonical_description}
                  </h3>
                  {selectedMaster.notes && (
                    <p className="text-xs text-slate-500 mt-1 italic">{selectedMaster.notes}</p>
                  )}
                </div>

                {/* Mapped Rates Table */}
                <div className="flex-1 overflow-y-auto">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                      Mapped Provincial Equivalents ({selectedMaster.mapped_rates?.length || 0})
                    </h4>
                  </div>

                  {!selectedMaster.mapped_rates || selectedMaster.mapped_rates.length === 0 ? (
                    <div className="text-center py-12 border border-dashed border-slate-200 rounded-xl">
                      <Link className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                      <p className="text-xs font-semibold text-slate-600">No provincial rate items mapped yet.</p>
                      <p className="text-[11px] text-slate-400 mt-0.5">
                        Switch to "Smart Suggestions" tab to review automated match candidates.
                      </p>
                    </div>
                  ) : (
                    <table className="w-full text-left text-xs border-collapse">
                      <thead className="bg-slate-50 text-slate-600 font-bold uppercase border-b border-slate-200">
                        <tr>
                          <th className="py-2.5 px-3">Province / District</th>
                          <th className="py-2.5 px-3">Code</th>
                          <th className="py-2.5 px-3">Original Description</th>
                          <th className="py-2.5 px-3 text-right">Rate (LKR)</th>
                          <th className="py-2.5 px-3 text-center">Unlink</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {selectedMaster.mapped_rates.map((rate) => (
                          <tr key={rate.id} className="hover:bg-slate-50">
                            <td className="py-2.5 px-3">
                              <div className="font-bold text-slate-800">{rate.province}</div>
                              <div className="text-[10px] text-slate-400">{rate.district} ({rate.year})</div>
                            </td>
                            <td className="py-2.5 px-3 font-mono font-bold text-blue-700">
                              {rate.item_code}
                            </td>
                            <td className="py-2.5 px-3 text-slate-700 truncate max-w-xs" title={rate.description || ''}>
                              {rate.description}
                            </td>
                            <td className="py-2.5 px-3 text-right font-mono font-bold text-slate-900">
                              {(rate.rate || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                            </td>
                            <td className="py-2.5 px-3 text-center">
                              <button
                                onClick={() => handleUnmap(rate.id)}
                                title="Unlink mapping"
                                className="p-1 text-slate-400 hover:text-rose-600 rounded"
                              >
                                <Unlink className="w-3.5 h-3.5" />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-full text-slate-400 text-xs">
                Select a master item from the left to view provincial mappings.
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Suggestions Tab */
        <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 space-y-4">
          <div className="border-b border-slate-100 pb-3">
            <h3 className="text-sm font-bold text-slate-900">Algorithmic Match Suggestions</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Items suggested based on high semantic and keyword similarity to Master Items.
              No automatic merge occurs without user approval.
            </p>
          </div>

          {suggestions.length === 0 ? (
            <div className="text-center py-12 text-slate-400 text-xs">
              <Check className="w-8 h-8 mx-auto text-emerald-500 mb-2" />
              <span>All candidate rate items are currently mapped or no strong suggestions found.</span>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-50 text-slate-600 font-bold uppercase border-b border-slate-200">
                  <tr>
                    <th className="py-2.5 px-3">Provincial Candidate</th>
                    <th className="py-2.5 px-3">Candidate Description</th>
                    <th className="py-2.5 px-3">Target Master Item</th>
                    <th className="py-2.5 px-3 text-center">Match Confidence</th>
                    <th className="py-2.5 px-3 text-center">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {suggestions.map((sugg, idx) => (
                    <tr key={idx} className="hover:bg-slate-50">
                      <td className="py-3 px-3">
                        <div className="font-mono font-bold text-blue-700">{sugg.rate_item.item_code}</div>
                        <div className="text-[10px] text-slate-500">{sugg.rate_item.province} • {sugg.rate_item.district}</div>
                      </td>
                      <td className="py-3 px-3 text-slate-800 font-medium">
                        {sugg.rate_item.description}
                      </td>
                      <td className="py-3 px-3">
                        <div className="font-mono font-bold text-slate-900">{sugg.master_code}</div>
                        <div className="text-[10px] text-slate-500 truncate max-w-xs">{sugg.canonical_description}</div>
                      </td>
                      <td className="py-3 px-3 text-center">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700">
                          {Math.round(sugg.similarity * 100)}% Match
                        </span>
                      </td>
                      <td className="py-3 px-3 text-center">
                        <button
                          onClick={() => handleApproveSuggestion(sugg)}
                          className="flex items-center gap-1 mx-auto px-2.5 py-1 bg-blue-600 hover:bg-blue-500 text-white font-bold text-[11px] rounded-lg shadow-xs"
                        >
                          <Check className="w-3 h-3" />
                          <span>Approve Mapping</span>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Create Master Item Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <form onSubmit={handleCreateMaster} className="bg-white rounded-2xl border border-slate-200 shadow-2xl p-6 max-w-md w-full space-y-4">
            <h3 className="text-base font-bold text-slate-900 border-b border-slate-100 pb-3">
              Create Canonical Master Item
            </h3>

            <div className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Sector</label>
                  <select
                    value={newSector}
                    onChange={(e) => {
                      setNewSector(e.target.value);
                      const sys = SECTOR_RATE_SYSTEM_MAP[e.target.value] || ['BSR'];
                      setNewRateSystem(sys[0]);
                    }}
                    className="w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-600 bg-white"
                  >
                    {SECTORS.map((s) => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Rate System</label>
                  <select
                    value={newRateSystem}
                    onChange={(e) => setNewRateSystem(e.target.value)}
                    className="w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-600 bg-white"
                  >
                    {(SECTOR_RATE_SYSTEM_MAP[newSector] || RATE_SYSTEMS).map((rs) => (
                      <option key={rs} value={rs}>{rs}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Master Code</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. M-BK01 or M-CONC01"
                  value={newCode}
                  onChange={(e) => setNewCode(e.target.value)}
                  className="w-full p-2 border border-slate-300 rounded-lg font-mono focus:ring-2 focus:ring-blue-600"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Canonical Description</label>
                <textarea
                  required
                  rows={3}
                  placeholder="Standard description (e.g. Brickwork in 225 mm 1:5 cement:sand mortar)"
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  className="w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-600"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Canonical Unit</label>
                  <input
                    type="text"
                    required
                    placeholder="m³, m², nr, kg..."
                    value={newUnit}
                    onChange={(e) => setNewUnit(e.target.value)}
                    className="w-full p-2 border border-slate-300 rounded-lg font-mono focus:ring-2 focus:ring-blue-600"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Category</label>
                  <input
                    type="text"
                    placeholder="Brick Layer, Concreter..."
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                    className="w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-600"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Notes (Optional)</label>
                <input
                  type="text"
                  placeholder="Standards reference, e.g. SLS 573"
                  value={newNotes}
                  onChange={(e) => setNewNotes(e.target.value)}
                  className="w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-600"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-4 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-xs font-bold bg-blue-600 hover:bg-blue-500 text-white rounded-lg shadow-xs"
              >
                Create Master Item
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
