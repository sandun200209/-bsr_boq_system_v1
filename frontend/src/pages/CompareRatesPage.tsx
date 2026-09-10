import React, { useState, useEffect } from 'react';
import {
  GitCompare,
  Filter,
  TrendingDown,
  TrendingUp,
  Search,
  RefreshCw,
  Layers,
} from 'lucide-react';
import { api } from '../api/client';
import { CompareResponse, FilterOptions } from '../types';
import { PROVINCE_LIST, SECTORS, RATE_SYSTEMS, SECTOR_RATE_SYSTEM_MAP, SECTOR_BADGE_CLASSES } from '../constants/sriLanka';

export const CompareRatesPage: React.FC = () => {
  // Filters
  const [sector, setSector] = useState<string>('Building Works');
  const [rateSystem, setRateSystem] = useState<string>('BSR');
  const [selectedProvinces, setSelectedProvinces] = useState<string[]>([]);
  const [selectedYears, setSelectedYears] = useState<number[]>([]);
  const [category, setCategory] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [baseItemId, setBaseItemId] = useState<number | undefined>(undefined);

  // State
  const [compareData, setCompareData] = useState<CompareResponse | null>(null);
  const [filterOpts, setFilterOpts] = useState<FilterOptions | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    api.getFilterOptions().then(setFilterOpts).catch(console.error);
  }, []);

  const handleSectorChange = (newSec: string) => {
    setSector(newSec);
    const systems = SECTOR_RATE_SYSTEM_MAP[newSec] || ['BSR'];
    setRateSystem(systems[0]);
  };

  const loadComparison = async () => {
    try {
      setLoading(true);
      const res = await api.getCompare({
        sector: sector || undefined,
        rate_system: rateSystem || undefined,
        provinces: selectedProvinces.length > 0 ? selectedProvinces : undefined,
        years: selectedYears.length > 0 ? selectedYears : undefined,
        category: category || undefined,
        q: searchQuery || undefined,
        base_item_id: baseItemId,
      });
      setCompareData(res);
    } catch (err) {
      console.error('Comparison error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadComparison();
  }, [sector, rateSystem, selectedProvinces, selectedYears, category, baseItemId]);

  const toggleProvince = (prov: string) => {
    setSelectedProvinces((prev) =>
      prev.includes(prov) ? prev.filter((p) => p !== prov) : [...prev, prov]
    );
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Page Title */}
      <div>
        <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Compare Rates</h2>
        <p className="text-xs text-slate-500 mt-1">
          Analyze price disparities between provinces, districts, years, and revisions.
          Select multiple regions simultaneously and assign any entry as the comparison base.
        </p>
      </div>

      {/* Filter and Criteria Card */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-5">
        <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-blue-600" />
          <span>Comparison Parameters</span>
        </h3>

        {/* Sector & Rate System Selector */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-slate-50/80 rounded-xl border border-slate-200">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center justify-between">
              <span>Sector Scope</span>
              <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium border ${SECTOR_BADGE_CLASSES[sector] || 'bg-slate-100 text-slate-700'}`}>
                {sector}
              </span>
            </label>
            <select
              value={sector}
              onChange={(e) => handleSectorChange(e.target.value)}
              className="w-full text-xs font-medium rounded-lg border border-slate-300 py-2 px-3 bg-white focus:outline-none focus:ring-2 focus:ring-blue-600"
            >
              {SECTORS.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Rate System
            </label>
            <select
              value={rateSystem}
              onChange={(e) => setRateSystem(e.target.value)}
              className="w-full text-xs font-medium rounded-lg border border-slate-300 py-2 px-3 bg-white focus:outline-none focus:ring-2 focus:ring-blue-600"
            >
              {(SECTOR_RATE_SYSTEM_MAP[sector] || RATE_SYSTEMS).map((rs) => (
                <option key={rs} value={rs}>{rs}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Multi-Province Selector Chips */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="block text-xs font-semibold text-slate-600">
              Select Provinces to Compare simultaneously {selectedProvinces.length > 0 ? `(${selectedProvinces.length} selected)` : '(All Provinces)'}:
            </label>
            {selectedProvinces.length > 0 && (
              <button
                type="button"
                onClick={() => setSelectedProvinces([])}
                className="text-xs font-semibold text-blue-600 hover:underline"
              >
                Clear selection (Show All)
              </button>
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            {PROVINCE_LIST.map((prov) => {
              const isSelected = selectedProvinces.includes(prov);
              return (
                <button
                  key={prov}
                  type="button"
                  onClick={() => toggleProvince(prov)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all border ${
                    isSelected
                      ? 'bg-blue-600 border-blue-600 text-white shadow-xs'
                      : 'bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100'
                  }`}
                >
                  {prov === 'All Provinces' ? 'All Provinces (National)' : prov}
                </button>
              );
            })}
          </div>
        </div>

        {/* Search Query, Category, and Year Row */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 pt-2 border-t border-slate-100">
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">
              Search Construction Work / Item
            </label>
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="e.g. Brickwork, Concrete, Excavation, DM01..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && loadComparison()}
                className="w-full pl-9 pr-3 py-2 text-xs rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-600"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">
              Category Filter
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full py-2 px-3 text-xs rounded-lg border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-blue-600"
            >
              <option value="">All Categories</option>
              {filterOpts?.categories.map((cat) => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">
              Year Filter
            </label>
            <select
              value={selectedYears[0] || ''}
              onChange={(e) => setSelectedYears(e.target.value ? [parseInt(e.target.value)] : [])}
              className="w-full py-2 px-3 text-xs rounded-lg border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-blue-600"
            >
              <option value="">All Years</option>
              {filterOpts?.years.map((yr) => (
                <option key={yr} value={yr}>{yr}</option>
              ))}
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={loadComparison}
              className="w-full flex items-center justify-center gap-2 py-2 px-4 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs rounded-lg shadow-xs transition-all"
            >
              {loading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <GitCompare className="w-3.5 h-3.5" />}
              <span>Execute Comparison</span>
            </button>
          </div>
        </div>
      </div>

      {/* Comparison Results */}
      {loading ? (
        <div className="p-12 text-center text-slate-400 flex flex-col items-center gap-3">
          <RefreshCw className="w-6 h-6 animate-spin text-blue-600" />
          <span className="text-xs font-medium">Computing price variance across provinces...</span>
        </div>
      ) : !compareData || compareData.groups.length === 0 ? (
        <div className="bg-white p-12 rounded-2xl border border-slate-200 text-center text-slate-500 space-y-2">
          <Layers className="w-8 h-8 text-slate-300 mx-auto" />
          <p className="font-semibold text-sm">No comparable rate items found.</p>
          <p className="text-xs text-slate-400">Try broadening your province selections or search keywords.</p>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>
              Comparing <strong>{compareData.total_items_compared}</strong> rates across{' '}
              <strong>{compareData.total_groups}</strong> distinct work specifications
            </span>
          </div>

          {compareData.groups.map((group) => (
            <div
              key={group.key}
              className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden"
            >
              {/* Group Summary Header */}
              <div className="p-5 bg-slate-50/80 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <h4 className="font-bold text-slate-900 text-sm">{group.title}</h4>
                    {group.key.startsWith('master_') ? (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                        Approved Master Item
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-600 border border-slate-300">
                        Single Unmapped Rate
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-slate-500 mt-0.5">
                    Unit: <span className="font-semibold font-mono text-slate-700">{group.unit || 'Unit'}</span>
                  </div>
                </div>

                {/* Summary Badges: Min, Max, Avg */}
                <div className="flex items-center gap-3 text-xs flex-wrap">
                  <div className="px-2.5 py-1 bg-white border border-slate-200 rounded-lg">
                    <span className="text-slate-500">Min: </span>
                    <span className="font-mono font-bold text-emerald-600">
                      LKR {group.min_rate.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </span>
                  </div>

                  <div className="px-2.5 py-1 bg-white border border-slate-200 rounded-lg">
                    <span className="text-slate-500">Avg: </span>
                    <span className="font-mono font-bold text-blue-600">
                      LKR {group.avg_rate.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </span>
                  </div>

                  <div className="px-2.5 py-1 bg-white border border-slate-200 rounded-lg">
                    <span className="text-slate-500">Max: </span>
                    <span className="font-mono font-bold text-rose-600">
                      LKR {group.max_rate.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </span>
                  </div>

                  <div className="px-2.5 py-1 bg-slate-100 rounded-lg text-slate-600 font-medium">
                    Spread: <span className="font-mono font-semibold">LKR {group.spread.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
                  </div>
                </div>
              </div>

              {/* Items Comparison Table */}
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-slate-100/50 text-slate-600 font-bold uppercase border-b border-slate-200">
                    <tr>
                      <th className="py-2.5 px-4">Base</th>
                      <th className="py-2.5 px-4">Province & District</th>
                      <th className="py-2.5 px-4">Year / Revision</th>
                      <th className="py-2.5 px-4">Code</th>
                      <th className="py-2.5 px-4 text-right">Rate (LKR)</th>
                      <th className="py-2.5 px-4 text-right">Difference (LKR)</th>
                      <th className="py-2.5 px-4 text-right">Diff (%)</th>
                      <th className="py-2.5 px-4">Source Reference</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {group.items.map((row) => (
                      <tr
                        key={row.id}
                        className={`transition-colors ${
                          row.is_base ? 'bg-blue-50/60 font-semibold' : 'hover:bg-slate-50'
                        }`}
                      >
                        {/* Base Radio Selection */}
                        <td className="py-3 px-4">
                          <label className="flex items-center gap-1.5 cursor-pointer">
                            <input
                              type="radio"
                              name={`base_${group.key}`}
                              checked={row.is_base}
                              onChange={() => setBaseItemId(row.id)}
                              className="text-blue-600 focus:ring-blue-500"
                            />
                            {row.is_base && (
                              <span className="text-[10px] font-bold text-blue-700 bg-blue-100 px-1.5 py-0.5 rounded">
                                Base
                              </span>
                            )}
                          </label>
                        </td>

                        {/* Region */}
                        <td className="py-3 px-4">
                          <div className="font-bold text-slate-900">{row.province}</div>
                          <div className="text-[11px] text-slate-500">{row.district}</div>
                        </td>

                        {/* Year / Revision */}
                        <td className="py-3 px-4">
                          <div className="font-semibold text-slate-800">{row.year}</div>
                          <div className="text-[11px] text-slate-500">{row.revision}</div>
                        </td>

                        {/* Code */}
                        <td className="py-3 px-4 font-mono font-bold text-blue-700">
                          {row.item_code || '-'}
                        </td>

                        {/* Rate */}
                        <td className="py-3 px-4 text-right font-mono font-bold text-slate-900 text-sm">
                          {row.rate.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </td>

                        {/* Difference LKR */}
                        <td className="py-3 px-4 text-right font-mono">
                          {row.is_base ? (
                            <span className="text-slate-400">-</span>
                          ) : (
                            <span
                              className={`font-semibold ${
                                row.diff_lkr > 0
                                  ? 'text-rose-600'
                                  : row.diff_lkr < 0
                                  ? 'text-emerald-600'
                                  : 'text-slate-500'
                              }`}
                            >
                              {row.diff_lkr > 0 ? `+${row.diff_lkr.toLocaleString('en-US', { minimumFractionDigits: 2 })}` : row.diff_lkr.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                            </span>
                          )}
                        </td>

                        {/* Difference % */}
                        <td className="py-3 px-4 text-right font-mono">
                          {row.is_base ? (
                            <span className="text-slate-400">Baseline</span>
                          ) : (
                            <span
                              className={`inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[11px] font-bold ${
                                row.diff_percent > 0
                                  ? 'bg-rose-50 text-rose-700'
                                  : row.diff_percent < 0
                                  ? 'bg-emerald-50 text-emerald-700'
                                  : 'bg-slate-100 text-slate-600'
                              }`}
                            >
                              {row.diff_percent > 0 ? (
                                <>
                                  <TrendingUp className="w-3 h-3 text-rose-500" />
                                  <span>+{row.diff_percent.toFixed(1)}%</span>
                                </>
                              ) : row.diff_percent < 0 ? (
                                <>
                                  <TrendingDown className="w-3 h-3 text-emerald-500" />
                                  <span>{row.diff_percent.toFixed(1)}%</span>
                                </>
                              ) : (
                                '0.0%'
                              )}
                            </span>
                          )}
                        </td>

                        {/* Source */}
                        <td className="py-3 px-4 text-slate-500 text-[11px] truncate max-w-xs">
                          {row.source_label}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
