import React, { useState, useEffect, useCallback } from 'react';
import {
  Search,
  Copy,
  Check,
  Filter,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  FileSpreadsheet,
  X,
  Download,
  ExternalLink,
} from 'lucide-react';
import { api } from '../api/client';
import { RateItem, FilterOptions } from '../types';
import { SECTORS, RATE_SYSTEMS, SECTOR_BADGE_CLASSES } from '../constants/sriLanka';

interface RateSearchPageProps {
  initialFilters?: any;
  onViewSource?: (fileId: number, page?: number) => void;
}

export const RateSearchPage: React.FC<RateSearchPageProps> = ({
  initialFilters,
  onViewSource,
}) => {
  // Query & Filters
  const [searchTerm, setSearchTerm] = useState<string>(initialFilters?.q || '');
  const [debouncedSearch, setDebouncedSearch] = useState<string>(initialFilters?.q || '');
  const [sector, setSector] = useState<string>(initialFilters?.sector || '');
  const [rateSystem, setRateSystem] = useState<string>(initialFilters?.rate_system || '');
  const [province, setProvince] = useState<string>(initialFilters?.province || '');
  const [district, setDistrict] = useState<string>(initialFilters?.district || '');
  const [year, setYear] = useState<string>(initialFilters?.year ? String(initialFilters.year) : '');
  const [revision, setRevision] = useState<string>(initialFilters?.revision || '');
  const [datasetType, setDatasetType] = useState<string>(initialFilters?.dataset_type || '');
  const [vatBasis, setVatBasis] = useState<string>(initialFilters?.vat_basis || '');
  const [category, setCategory] = useState<string>(initialFilters?.category || '');
  const [status, setStatus] = useState<string>('ALL');
  const [pageNumber, setPageNumber] = useState<string>('');
  const [sheet, setSheet] = useState<string>('');

  // Sorting & Pagination (Default to book order id asc)
  const [sortBy, setSortBy] = useState<string>('id');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(25);

  // Data State
  const [results, setResults] = useState<RateItem[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(false);
  const [filterOpts, setFilterOpts] = useState<FilterOptions | null>(null);

  // Copy notification state
  const [copiedId, setCopiedId] = useState<number | null>(null);
  const [copyToast, setCopyToast] = useState<string | null>(null);

  // Selection state
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());

  // Debounce search input (300ms)
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchTerm);
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  // Load filter options on mount
  useEffect(() => {
    api.getFilterOptions().then(setFilterOpts).catch(console.error);
  }, []);

  // Fetch search results
  const fetchRates = useCallback(async () => {
    try {
      setLoading(true);
      const res = await api.searchRates({
        q: debouncedSearch || undefined,
        sector: sector || undefined,
        rate_system: rateSystem || undefined,
        province: province || undefined,
        district: district || undefined,
        year: year ? parseInt(year) : undefined,
        revision: revision || undefined,
        dataset_type: datasetType || undefined,
        vat_basis: vatBasis || undefined,
        category: category || undefined,
        status: status || undefined,
        source_page: pageNumber ? parseInt(pageNumber) : undefined,
        sheet: sheet || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
        page,
        page_size: pageSize,
      });
      setResults(res.items);
      setTotal(res.total);
      setTotalPages(res.pages);
    } catch (err) {
      console.error('Search failed:', err);
    } finally {
      setLoading(false);
    }
  }, [debouncedSearch, sector, rateSystem, province, district, year, revision, datasetType, vatBasis, category, status, pageNumber, sheet, sortBy, sortOrder, page, pageSize]);

  useEffect(() => {
    fetchRates();
  }, [fetchRates]);

  // Selection helpers
  const allVisibleSelected = results.length > 0 && results.every((it) => selectedIds.has(it.id));
  const someVisibleSelected = results.some((it) => selectedIds.has(it.id));

  const handleToggleSelectAll = () => {
    if (allVisibleSelected) {
      const next = new Set(selectedIds);
      results.forEach((it) => next.delete(it.id));
      setSelectedIds(next);
    } else {
      const next = new Set(selectedIds);
      results.forEach((it) => next.add(it.id));
      setSelectedIds(next);
    }
  };

  const handleToggleSelectItem = (id: number) => {
    const next = new Set(selectedIds);
    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
    }
    setSelectedIds(next);
  };

  const handleClearSelection = () => {
    setSelectedIds(new Set());
  };

  const handleSelectAllAcrossResults = async () => {
    try {
      setLoading(true);
      const res = await api.searchRates({
        q: debouncedSearch || undefined,
        province: province || undefined,
        district: district || undefined,
        year: year ? parseInt(year) : undefined,
        revision: revision || undefined,
        dataset_type: datasetType || undefined,
        vat_basis: vatBasis || undefined,
        category: category || undefined,
        status: status || undefined,
        source_page: pageNumber ? parseInt(pageNumber) : undefined,
        sheet: sheet || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
        page: 1,
        page_size: Math.min(total, 500),
      });
      const allIds = new Set(res.items.map((it) => it.id));
      setSelectedIds(allIds);
      setCopyToast(`Selected all ${res.items.length} matching items!`);
      setTimeout(() => setCopyToast(null), 3500);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const copyItemsToClipboard = async (format: 'excel' | 'text' | 'codes', useAllVisible: boolean = false) => {
    let itemsToCopy: RateItem[] = [];
    if (useAllVisible) {
      itemsToCopy = results;
    } else if (selectedIds.size > results.length) {
      // User selected across pages: fetch all matching selected items
      try {
        setLoading(true);
        const res = await api.searchRates({
          q: debouncedSearch || undefined,
          province: province || undefined,
          district: district || undefined,
          year: year ? parseInt(year) : undefined,
          revision: revision || undefined,
          dataset_type: datasetType || undefined,
          vat_basis: vatBasis || undefined,
          category: category || undefined,
          status: status || undefined,
          source_page: pageNumber ? parseInt(pageNumber) : undefined,
          sheet: sheet || undefined,
          sort_by: sortBy,
          sort_order: sortOrder,
          page: 1,
          page_size: Math.min(total, 500),
        });
        itemsToCopy = res.items.filter((it) => selectedIds.has(it.id));
      } catch (e) {
        itemsToCopy = results.filter((it) => selectedIds.has(it.id));
      } finally {
        setLoading(false);
      }
    } else if (selectedIds.size > 0) {
      itemsToCopy = results.filter((it) => selectedIds.has(it.id));
    } else {
      itemsToCopy = results;
    }

    if (!itemsToCopy.length) return;

    let textToCopy = '';
    if (format === 'excel') {
      const header = ['Item Code', 'Description', 'Unit', 'Rate (LKR)', 'Province', 'District', 'Year', 'Revision', 'Source Sheet / Page'].join('\t');
      const rows = itemsToCopy.map((it) => [
        it.item_code || '',
        (it.description || '').replace(/\r?\n|\r/g, ' '),
        it.unit || '',
        it.rate !== null && it.rate !== undefined ? it.rate : '',
        it.province || '',
        it.district || '',
        it.year || '',
        it.revision || '',
        it.source_page ? `Page ${it.source_page}` : (it.source_sheet ? `${it.source_sheet} R${it.source_row || ''}` : ''),
      ].join('\t'));
      textToCopy = [header, ...rows].join('\n');
    } else if (format === 'text') {
      textToCopy = itemsToCopy.map((it) =>
        `${it.item_code || 'ITEM'} - ${it.description || ''} (${it.unit || '-'}): LKR ${(it.rate || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}`
      ).join('\n');
    } else if (format === 'codes') {
      textToCopy = itemsToCopy.map((it) => it.item_code).filter(Boolean).join(', ');
    }

    await navigator.clipboard.writeText(textToCopy);
    setCopyToast(`Copied ${itemsToCopy.length} items to clipboard (${format === 'excel' ? 'Tab-separated for Excel' : format})!`);
    setTimeout(() => setCopyToast(null), 3500);
  };

  const handleCopy = (item: RateItem) => {
    const textToCopy = `${item.item_code || ''} - ${item.description || ''} (${item.unit || ''}): LKR ${(item.rate || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
    navigator.clipboard.writeText(textToCopy);
    setCopiedId(item.id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleSort = (col: string) => {
    if (sortBy === col) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(col);
      setSortOrder('asc');
    }
    setPage(1);
  };

  const resetFilters = () => {
    setSearchTerm('');
    setSector('');
    setRateSystem('');
    setProvince('');
    setDistrict('');
    setYear('');
    setRevision('');
    setDatasetType('');
    setVatBasis('');
    setCategory('');
    setStatus('ALL');
    setPageNumber('');
    setSheet('');
    setSelectedIds(new Set());
    setSortBy('id');
    setSortOrder('asc');
    setPage(1);
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Rate Search</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Instant trigram & full-text query engine across {total.toLocaleString()} rate items
          </p>
        </div>

        {/* Live Search Input */}
        <div className="relative w-full md:w-96">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
          <input
            type="text"
            placeholder="Search code, description, keywords (e.g. BK01, 225mm, mortar)..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-white text-sm rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-blue-600 shadow-xs"
          />
          {loading && (
            <RefreshCw className="w-3.5 h-3.5 text-blue-600 animate-spin absolute right-3.5 top-3.5" />
          )}
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-bold text-slate-700 uppercase tracking-wider">
            <Filter className="w-3.5 h-3.5 text-blue-600" />
            <span>Filters</span>
          </div>
          <button
            onClick={resetFilters}
            className="text-xs text-blue-600 hover:text-blue-800 font-semibold"
          >
            Reset Filters
          </button>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-11 gap-2.5">
          {/* Sector */}
          <select
            value={sector}
            onChange={(e) => { setSector(e.target.value); setPage(1); }}
            className="text-xs rounded-lg border border-slate-300 py-1.5 px-2 bg-white focus:outline-none focus:ring-1 focus:ring-blue-600 font-medium text-slate-800 truncate"
            title={sector || 'All Sectors'}
          >
            <option value="">All Sectors</option>
            {(filterOpts?.sectors || SECTORS).map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>

          {/* Rate System */}
          <select
            value={rateSystem}
            onChange={(e) => { setRateSystem(e.target.value); setPage(1); }}
            className="text-xs rounded-lg border border-slate-300 py-1.5 px-2 bg-white focus:outline-none focus:ring-1 focus:ring-blue-600 font-medium text-slate-800 truncate"
            title={rateSystem || 'All Systems'}
          >
            <option value="">All Systems</option>
            {(filterOpts?.rate_systems || RATE_SYSTEMS).map((rs) => (
              <option key={rs} value={rs}>{rs}</option>
            ))}
          </select>

          {/* Province */}
          <select
            value={province}
            onChange={(e) => { setProvince(e.target.value); setDistrict(''); setPage(1); }}
            className="text-xs rounded-lg border border-slate-300 py-1.5 px-2 bg-white focus:outline-none focus:ring-1 focus:ring-blue-600"
          >
            <option value="">All Provinces</option>
            {filterOpts?.provinces.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>

          {/* District */}
          <select
            value={district}
            onChange={(e) => { setDistrict(e.target.value); setPage(1); }}
            className="text-xs rounded-lg border border-slate-300 py-1.5 px-2 bg-white focus:outline-none focus:ring-1 focus:ring-blue-600"
          >
            <option value="">All Districts</option>
            {filterOpts?.districts.map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>

          {/* Year */}
          <select
            value={year}
            onChange={(e) => { setYear(e.target.value); setPage(1); }}
            className="text-xs rounded-lg border border-slate-300 py-1.5 px-2 bg-white focus:outline-none focus:ring-1 focus:ring-blue-600"
          >
            <option value="">All Years</option>
            {filterOpts?.years.map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>

          {/* Revision */}
          <select
            value={revision}
            onChange={(e) => { setRevision(e.target.value); setPage(1); }}
            className="text-xs rounded-lg border border-slate-300 py-1.5 px-2 bg-white focus:outline-none focus:ring-1 focus:ring-blue-600"
          >
            <option value="">All Revisions</option>
            {filterOpts?.revisions.map((r) => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>

          {/* Category */}
          <select
            value={category}
            onChange={(e) => { setCategory(e.target.value); setPage(1); }}
            className="text-xs rounded-lg border border-slate-300 py-1.5 px-2 bg-white focus:outline-none focus:ring-1 focus:ring-blue-600"
          >
            <option value="">All Categories</option>
            {filterOpts?.categories.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>

          {/* VAT Basis */}
          <select
            value={vatBasis}
            onChange={(e) => { setVatBasis(e.target.value); setPage(1); }}
            className="text-xs rounded-lg border border-slate-300 py-1.5 px-2 bg-white focus:outline-none focus:ring-1 focus:ring-blue-600"
          >
            <option value="">All VAT</option>
            {filterOpts?.vat_bases.map((v) => (
              <option key={v} value={v}>{v}</option>
            ))}
          </select>

          {/* Sheet */}
          <select
            value={sheet}
            onChange={(e) => { setSheet(e.target.value); setPage(1); }}
            className="text-xs rounded-lg border border-slate-300 py-1.5 px-2 bg-white focus:outline-none focus:ring-1 focus:ring-blue-600 truncate"
            title={sheet || 'All Sheets'}
          >
            <option value="">All Sheets</option>
            {filterOpts?.sheets?.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>

          {/* Status */}
          <select
            value={status}
            onChange={(e) => { setStatus(e.target.value); setPage(1); }}
            className="text-xs rounded-lg border border-slate-300 py-1.5 px-2 bg-white focus:outline-none focus:ring-1 focus:ring-blue-600"
          >
            <option value="ALL">All Statuses</option>
            <option value="VALID">Valid</option>
            <option value="APPROVED">Approved</option>
            <option value="NEEDS_REVIEW">Needs Review</option>
          </select>

          {/* Page Number */}
          <input
            type="number"
            min="1"
            placeholder="Page # (PDF)"
            value={pageNumber}
            onChange={(e) => { setPageNumber(e.target.value); setPage(1); }}
            className="text-xs rounded-lg border border-slate-300 py-1.5 px-2 bg-white focus:outline-none focus:ring-1 focus:ring-blue-600 w-full font-mono"
          />
        </div>
      </div>

      {/* Selection & Bulk Copy Action Bar */}
      <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-xs flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 cursor-pointer select-none font-semibold text-slate-700">
            <input
              type="checkbox"
              checked={allVisibleSelected}
              ref={(input) => {
                if (input) input.indeterminate = someVisibleSelected && !allVisibleSelected;
              }}
              onChange={handleToggleSelectAll}
              className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 w-4 h-4 cursor-pointer"
            />
            <span>Select All on Page ({results.length})</span>
          </label>

          {selectedIds.size > 0 && (
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold bg-blue-100 text-blue-800">
              {selectedIds.size} selected
            </span>
          )}

          {selectedIds.size > 0 && selectedIds.size < total && total <= 500 && (
            <button
              onClick={handleSelectAllAcrossResults}
              className="text-xs text-blue-600 hover:text-blue-800 font-semibold underline"
            >
              Select all {total} matching items across all pages
            </button>
          )}

          {selectedIds.size > 0 && (
            <button
              onClick={handleClearSelection}
              className="text-xs text-slate-500 hover:text-slate-800 flex items-center gap-1 font-medium"
            >
              <X className="w-3.5 h-3.5" />
              <span>Clear selection</span>
            </button>
          )}
        </div>

        <div className="flex items-center gap-2">
          {selectedIds.size > 0 ? (
            <>
              <button
                onClick={() => copyItemsToClipboard('excel', false)}
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-semibold shadow-xs transition-colors"
                title="Copy selected rows as tab-separated values ready to paste into Microsoft Excel"
              >
                <FileSpreadsheet className="w-3.5 h-3.5" />
                <span>Copy Selected ({selectedIds.size}) for Excel</span>
              </button>

              <button
                onClick={() => copyItemsToClipboard('text', false)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-slate-300 hover:bg-slate-100 text-slate-700 font-medium transition-colors"
                title="Copy selected rows as formatted text lines"
              >
                <Copy className="w-3.5 h-3.5 text-slate-500" />
                <span>Copy as Text</span>
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => copyItemsToClipboard('excel', true)}
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white font-semibold shadow-xs transition-colors"
                title="Copy all visible rows as tab-separated values ready to paste into Microsoft Excel"
              >
                <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400" />
                <span>Copy All Visible ({results.length}) for Excel</span>
              </button>

              <button
                onClick={() => copyItemsToClipboard('text', true)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-slate-300 hover:bg-slate-100 text-slate-700 font-medium transition-colors"
                title="Copy all visible rows as formatted text lines"
              >
                <Copy className="w-3.5 h-3.5 text-slate-500" />
                <span>Copy All as Text</span>
              </button>
            </>
          )}
        </div>
      </div>

      {/* Results Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-slate-100 text-slate-700 font-bold uppercase sticky top-0 z-10 border-b border-slate-200 shadow-2xs">
              <tr>
                <th className="py-3 px-3 w-10 text-center">
                  <input
                    type="checkbox"
                    checked={allVisibleSelected}
                    ref={(input) => {
                      if (input) input.indeterminate = someVisibleSelected && !allVisibleSelected;
                    }}
                    onChange={handleToggleSelectAll}
                    title="Select/Deselect All on Page"
                    className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 w-4 h-4 cursor-pointer"
                  />
                </th>
                <th
                  onClick={() => handleSort('item_code')}
                  className="py-3 px-3 cursor-pointer hover:bg-slate-200/80 transition-colors w-24"
                >
                  Code {sortBy === 'item_code' && (sortOrder === 'asc' ? '↑' : '↓')}
                </th>
                <th
                  onClick={() => handleSort('description')}
                  className="py-3 px-4 cursor-pointer hover:bg-slate-200/80 transition-colors min-w-[280px]"
                >
                  Description {sortBy === 'description' && (sortOrder === 'asc' ? '↑' : '↓')}
                </th>
                <th className="py-3 px-3 w-16">Unit</th>
                <th
                  onClick={() => handleSort('rate')}
                  className="py-3 px-4 cursor-pointer hover:bg-slate-200/80 transition-colors text-right w-28"
                >
                  Rate (LKR) {sortBy === 'rate' && (sortOrder === 'asc' ? '↑' : '↓')}
                </th>
                <th className="py-3 px-3 min-w-[140px]">Region</th>
                <th className="py-3 px-3 w-28">Year / Rev</th>
                <th className="py-3 px-3 min-w-[140px]">Source Reference</th>
                <th className="py-3 px-3 text-center w-16">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {results.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-400">
                    {loading ? (
                      <div className="flex items-center justify-center gap-2">
                        <RefreshCw className="w-4 h-4 animate-spin text-blue-600" />
                        <span>Searching BSR records...</span>
                      </div>
                    ) : (
                      <span>No matching rate items found. Try adjusting your filters.</span>
                    )}
                  </td>
                </tr>
              ) : (
                results.map((item) => (
                  <tr
                    key={item.id}
                    className={`hover:bg-slate-50 transition-colors group ${
                      selectedIds.has(item.id) ? 'bg-blue-50/70' : ''
                    }`}
                  >
                    {/* Selection Checkbox */}
                    <td className="py-3 px-3 text-center">
                      <input
                        type="checkbox"
                        checked={selectedIds.has(item.id)}
                        onChange={() => handleToggleSelectItem(item.id)}
                        className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 w-4 h-4 cursor-pointer"
                      />
                    </td>

                    {/* Code */}
                    <td className="py-3 px-3 font-mono font-bold text-blue-700">
                      {item.item_code || <span className="text-slate-400 italic">No Code</span>}
                    </td>

                    {/* Description */}
                    <td className="py-3 px-4 text-slate-900 leading-relaxed font-normal">
                      <div className="font-medium">{item.description}</div>
                      <div className="flex flex-wrap items-center gap-1.5 mt-1">
                        {item.sector && (
                          <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold border ${SECTOR_BADGE_CLASSES[item.sector] || 'bg-slate-100 text-slate-700'}`}>
                            {item.rate_system || item.sector.split(' ')[0]}
                          </span>
                        )}
                        {item.category_name && (
                          <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-600 text-[10px] font-semibold">
                            {item.category_name}
                          </span>
                        )}
                      </div>
                    </td>

                    {/* Unit */}
                    <td className="py-3 px-3 font-medium text-slate-700 font-mono">
                      {item.unit || '-'}
                    </td>

                    {/* Rate */}
                    <td className="py-3 px-4 text-right font-mono font-bold text-slate-900 text-sm">
                      {item.rate !== null && item.rate !== undefined ? (
                        item.rate.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
                      ) : (
                        <span className="text-rose-500 italic">N/A</span>
                      )}
                    </td>

                    {/* Region */}
                    <td className="py-3 px-3 text-slate-800">
                      <div className="font-medium">{item.district}</div>
                      <div className="text-[10px] text-slate-500">{item.province}</div>
                    </td>

                    {/* Year / Rev */}
                    <td className="py-3 px-3 text-slate-800">
                      <div className="font-semibold">{item.year}</div>
                      <div className="text-[10px] text-slate-500 truncate max-w-[100px]" title={item.revision}>
                        {item.revision}
                      </div>
                    </td>

                    {/* Source Reference */}
                    <td className="py-3 px-3 text-slate-600">
                      <div className="flex items-center justify-between gap-1">
                        <div
                          onClick={() => onViewSource && onViewSource(item.source_file_id, item.source_page || undefined)}
                          className={`font-medium truncate max-w-[140px] ${onViewSource ? 'cursor-pointer hover:text-blue-600' : ''}`}
                          title={item.original_filename || 'Source'}
                        >
                          {item.original_filename || 'Source Document'}
                        </div>
                        <div className="flex items-center gap-1 shrink-0">
                          <a
                            href={`/api/documents/${item.source_file_id}/download`}
                            target="_blank"
                            rel="noreferrer"
                            title="Download original file"
                            className="p-1 text-slate-400 hover:text-blue-600 hover:bg-slate-100 rounded"
                          >
                            <Download className="w-3.5 h-3.5" />
                          </a>
                          <a
                            href={`/api/documents/${item.source_file_id}/view`}
                            target="_blank"
                            rel="noreferrer"
                            title="View document"
                            className="p-1 text-slate-400 hover:text-blue-600 hover:bg-slate-100 rounded"
                          >
                            <ExternalLink className="w-3.5 h-3.5" />
                          </a>
                        </div>
                      </div>
                      <div className="flex flex-wrap items-center gap-1.5 mt-0.5">
                        {item.source_sheet && (
                          <span
                            className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200"
                            title={`Sheet: ${item.source_sheet} ${item.source_row ? `Row ${item.source_row}` : ''}`}
                          >
                            Sheet: {item.source_sheet.length > 20 ? item.source_sheet.slice(0, 18) + '...' : item.source_sheet} {item.source_row ? `R${item.source_row}` : ''}
                          </span>
                        )}
                        {item.source_page && (
                          <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                            Page {item.source_page}
                          </span>
                        )}
                        {!item.source_sheet && !item.source_page && (
                          <span className="text-[10px] text-slate-400">Archive</span>
                        )}
                      </div>
                    </td>

                    {/* Copy Button */}
                    <td className="py-3 px-3 text-center">
                      <button
                        onClick={() => handleCopy(item)}
                        title="Copy item details to clipboard"
                        className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-all"
                      >
                        {copiedId === item.id ? (
                          <Check className="w-4 h-4 text-emerald-600" />
                        ) : (
                          <Copy className="w-4 h-4" />
                        )}
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="p-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between text-xs text-slate-600">
          <div>
            Showing <span className="font-semibold">{results.length > 0 ? (page - 1) * pageSize + 1 : 0}</span> to{' '}
            <span className="font-semibold">{Math.min(page * pageSize, total)}</span> of{' '}
            <span className="font-semibold">{total.toLocaleString()}</span> entries
          </div>

          <div className="flex items-center gap-2">
            <select
              value={pageSize}
              onChange={(e) => { setPageSize(parseInt(e.target.value)); setPage(1); }}
              className="text-xs rounded border border-slate-300 py-1 px-2 bg-white"
            >
              <option value={25}>25 per page</option>
              <option value={50}>50 per page</option>
              <option value={100}>100 per page</option>
            </select>

            <div className="flex items-center gap-1">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className={`p-1.5 rounded border border-slate-300 ${
                  page <= 1 ? 'opacity-40 cursor-not-allowed bg-slate-100' : 'hover:bg-white bg-slate-50'
                }`}
              >
                <ChevronLeft className="w-3.5 h-3.5" />
              </button>

              <span className="px-2 font-medium">
                Page {page} of {totalPages}
              </span>

              <button
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                className={`p-1.5 rounded border border-slate-300 ${
                  page >= totalPages ? 'opacity-40 cursor-not-allowed bg-slate-100' : 'hover:bg-white bg-slate-50'
                }`}
              >
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {copyToast && (
        <div className="fixed bottom-6 right-6 z-50 bg-slate-900 text-white px-4 py-3 rounded-xl shadow-2xl flex items-center gap-3 border border-slate-700 animate-in fade-in slide-in-from-bottom-4">
          <Check className="w-4 h-4 text-emerald-400 shrink-0" />
          <span className="text-xs font-medium">{copyToast}</span>
        </div>
      )}
    </div>
  );
};
