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
  Layers,
} from 'lucide-react';
import { api } from '../api/client';
import { RateItem, FilterOptions } from '../types';
import { RATE_SYSTEMS, SECTOR_BADGE_CLASSES } from '../constants/sriLanka';
import { CESMMMappingModal } from '../components/CESMM/CESMMMappingModal';

interface RateSearchPageProps {
  initialFilters?: any;
  onViewSource?: (fileId: number, page?: number) => void;
  onNavigate?: (tab: string, params?: any) => void;
}

export const RateSearchPage: React.FC<RateSearchPageProps> = ({
  initialFilters,
  onViewSource,
  onNavigate,
}) => {
  // Query & Filters
  const [searchTerm, setSearchTerm] = useState<string>(initialFilters?.q || '');
  const [debouncedSearch, setDebouncedSearch] = useState<string>(initialFilters?.q || '');
  const [sector, setSector] = useState<string>(initialFilters?.sector || '');
  const [rateSystem, setRateSystem] = useState<string>(initialFilters?.rate_system || '');
  const [cesmmSectionNo, setCesmmSectionNo] = useState<string>(initialFilters?.cesmm_section_no || '');
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

  // Modal for CESMM Mapping
  const [cesmmModalItem, setCesmmModalItem] = useState<RateItem | null>(null);

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

  // Dynamically load cascading filter options as selections change
  useEffect(() => {
    api.getFilterOptions({
      rate_system: rateSystem || undefined,
      cesmm_section_no: cesmmSectionNo || undefined,
      category: category || undefined,
      province: province || undefined,
      district: district || undefined,
      year: year ? parseInt(year) : undefined,
      revision: revision || undefined,
      vat_basis: vatBasis || undefined,
      sheet: sheet || undefined,
      status: status && status !== 'ALL' ? status : undefined,
      sector: sector || undefined,
    }).then(setFilterOpts).catch(console.error);
  }, [rateSystem, cesmmSectionNo, category, province, district, year, revision, vatBasis, sheet, status, sector]);

  // Fetch search results
  const fetchRates = useCallback(async () => {
    try {
      setLoading(true);
      const res = await api.searchRates({
        q: debouncedSearch || undefined,
        sector: sector || undefined,
        rate_system: rateSystem || undefined,
        cesmm_section_no: cesmmSectionNo || undefined,
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
  }, [debouncedSearch, sector, rateSystem, cesmmSectionNo, province, district, year, revision, datasetType, vatBasis, category, status, pageNumber, sheet, sortBy, sortOrder, page, pageSize]);

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
        sector: sector || undefined,
        rate_system: rateSystem || undefined,
        cesmm_section_no: cesmmSectionNo || undefined,
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
          sector: sector || undefined,
          rate_system: rateSystem || undefined,
          cesmm_section_no: cesmmSectionNo || undefined,
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

  // Cascading enabled / satisfied states
  const isRateBookSelected = Boolean(rateSystem);
  const isCesmmEnabled = isRateBookSelected;
  const isCesmmSelected = Boolean(isCesmmEnabled && cesmmSectionNo);

  const isCategoryEnabled = isCesmmSelected;
  const isCategorySelected = Boolean(isCategoryEnabled && category);

  const isProvinceEnabled = isCategorySelected;
  const isProvinceSelected = Boolean(isProvinceEnabled && province);

  const isDistrictEnabled = isProvinceSelected;
  const isDistrictSelected = Boolean(isDistrictEnabled && district);

  const isYearEnabled = isDistrictSelected;
  const isYearSelected = Boolean(isYearEnabled && year);

  const isRevisionEnabled = isYearSelected;
  const isRevisionSelected = Boolean(isRevisionEnabled && revision);

  const isVatEnabled = isRevisionSelected;
  const isVatSelected = Boolean(isVatEnabled && vatBasis);

  const hasSheets = (filterOpts?.sheets?.length ?? 0) > 0;
  const isSheetEnabled = isVatSelected && hasSheets;
  const isSheetSatisfied = isVatSelected && (!hasSheets || Boolean(sheet));

  const isStatusEnabled = isSheetSatisfied;
  const isPageEnabled = isStatusEnabled;

  // Strict Reset-on-Change handlers: each resets all downstream child filters
  const handleRateSystemChange = (val: string) => {
    setRateSystem(val);
    setCesmmSectionNo('');
    setCategory('');
    setProvince('');
    setDistrict('');
    setYear('');
    setRevision('');
    setVatBasis('');
    setSheet('');
    setStatus('ALL');
    setPageNumber('');
    setPage(1);
  };

  const handleCesmmChange = (val: string) => {
    setCesmmSectionNo(val);
    setCategory('');
    setProvince('');
    setDistrict('');
    setYear('');
    setRevision('');
    setVatBasis('');
    setSheet('');
    setStatus('ALL');
    setPageNumber('');
    setPage(1);
  };

  const handleCategoryChange = (val: string) => {
    setCategory(val);
    setProvince('');
    setDistrict('');
    setYear('');
    setRevision('');
    setVatBasis('');
    setSheet('');
    setStatus('ALL');
    setPageNumber('');
    setPage(1);
  };

  const handleProvinceChange = (val: string) => {
    setProvince(val);
    setDistrict('');
    setYear('');
    setRevision('');
    setVatBasis('');
    setSheet('');
    setStatus('ALL');
    setPageNumber('');
    setPage(1);
  };

  const handleDistrictChange = (val: string) => {
    setDistrict(val);
    setYear('');
    setRevision('');
    setVatBasis('');
    setSheet('');
    setStatus('ALL');
    setPageNumber('');
    setPage(1);
  };

  const handleYearChange = (val: string) => {
    setYear(val);
    setRevision('');
    setVatBasis('');
    setSheet('');
    setStatus('ALL');
    setPageNumber('');
    setPage(1);
  };

  const handleRevisionChange = (val: string) => {
    setRevision(val);
    setVatBasis('');
    setSheet('');
    setStatus('ALL');
    setPageNumber('');
    setPage(1);
  };

  const handleVatChange = (val: string) => {
    setVatBasis(val);
    setSheet('');
    setStatus('ALL');
    setPageNumber('');
    setPage(1);
  };

  const handleSheetChange = (val: string) => {
    setSheet(val);
    setStatus('ALL');
    setPageNumber('');
    setPage(1);
  };

  const handleStatusChange = (val: string) => {
    setStatus(val);
    setPageNumber('');
    setPage(1);
  };

  const resetFilters = () => {
    setSearchTerm('');
    setDebouncedSearch('');
    setSector('');
    setRateSystem('');
    setCesmmSectionNo('');
    setCategory('');
    setProvince('');
    setDistrict('');
    setYear('');
    setRevision('');
    setDatasetType('');
    setVatBasis('');
    setSheet('');
    setStatus('ALL');
    setPageNumber('');
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
            Strict cascading query engine across {total.toLocaleString()} rate items
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
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800 uppercase tracking-wider">
              <Filter className="w-3.5 h-3.5 text-blue-600" />
              <span>Cascading Filters (Strict Flow 1 → 11)</span>
            </div>
            {filterOpts?.total_matching !== undefined && (
              <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                {filterOpts.total_matching.toLocaleString()} matching
              </span>
            )}
          </div>
          <button
            onClick={resetFilters}
            className="text-xs text-blue-600 hover:text-blue-800 font-semibold flex items-center gap-1 transition-colors"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Reset Filters</span>
          </button>
        </div>

        {/* Step Progression Breadcrumb */}
        <div className="flex items-center gap-1.5 overflow-x-auto text-[11px] py-1 border-y border-slate-100 no-scrollbar">
          {[
            { step: 1, name: 'Rate Book', active: isRateBookSelected },
            { step: 2, name: 'CESMM-SL', active: isCesmmSelected },
            { step: 3, name: 'Category', active: isCategorySelected },
            { step: 4, name: 'Province', active: isProvinceSelected },
            { step: 5, name: 'District', active: isDistrictSelected },
            { step: 6, name: 'Year', active: isYearSelected },
            { step: 7, name: 'Revision', active: isRevisionSelected },
            { step: 8, name: 'VAT', active: isVatSelected },
            { step: 9, name: 'Sheet', active: isSheetSatisfied },
            { step: 10, name: 'Status', active: isStatusEnabled && status !== 'ALL' },
            { step: 11, name: 'Page', active: Boolean(pageNumber) },
          ].map((item, idx) => (
            <React.Fragment key={item.step}>
              {idx > 0 && <span className="text-slate-300 text-[10px]">→</span>}
              <span
                className={`px-1.5 py-0.5 rounded font-mono text-[10px] whitespace-nowrap transition-colors ${
                  item.active
                    ? 'bg-blue-600 text-white font-bold shadow-2xs'
                    : (item.step === 1 || (item.step === 2 && isCesmmEnabled) || (item.step === 3 && isCategoryEnabled) || (item.step === 4 && isProvinceEnabled) || (item.step === 5 && isDistrictEnabled) || (item.step === 6 && isYearEnabled) || (item.step === 7 && isRevisionEnabled) || (item.step === 8 && isVatEnabled) || (item.step === 9 && isSheetEnabled) || (item.step === 10 && isStatusEnabled) || (item.step === 11 && isPageEnabled))
                    ? 'bg-blue-50 text-blue-700 font-semibold border border-blue-200'
                    : 'bg-slate-100 text-slate-400 select-none'
                }`}
              >
                {item.step}. {item.name}
              </span>
            </React.Fragment>
          ))}
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-11 gap-2.5">
          {/* 1: Rate Book */}
          <select
            value={rateSystem}
            onChange={(e) => handleRateSystemChange(e.target.value)}
            className="text-xs rounded-lg border border-blue-400 py-1.5 px-2 bg-blue-50/50 focus:outline-none focus:ring-2 focus:ring-blue-600 font-bold text-blue-950 truncate shadow-2xs cursor-pointer"
            title={rateSystem ? `Rate Book: ${rateSystem}` : 'Step 1: Select Rate Book'}
          >
            <option value="">1. [Select Rate Book]</option>
            {(filterOpts?.rate_systems || RATE_SYSTEMS).map((rs) => (
              <option key={rs} value={rs}>{rs}</option>
            ))}
          </select>

          {/* 2: CESMM Section */}
          <select
            value={cesmmSectionNo}
            disabled={!isCesmmEnabled}
            onChange={(e) => handleCesmmChange(e.target.value)}
            className={`text-xs rounded-lg py-1.5 px-2 font-medium truncate transition-colors ${
              isCesmmEnabled
                ? 'border border-indigo-400 bg-indigo-50/60 text-indigo-950 focus:outline-none focus:ring-2 focus:ring-indigo-600 cursor-pointer font-semibold shadow-2xs'
                : 'border border-slate-200 bg-slate-100 text-slate-400 cursor-not-allowed select-none'
            }`}
            title={cesmmSectionNo ? `CESMM Section ${cesmmSectionNo}` : (isCesmmEnabled ? 'Step 2: Select CESMM Section' : 'Step 2: Disabled (Select Rate Book first)')}
          >
            <option value="">{isCesmmEnabled ? '2. [Select CESMM Section]' : '2. CESMM (Locked)'}</option>
            {filterOpts?.cesmm_sections?.map((cs) => (
              <option key={cs.id} value={cs.section_no}>
                {cs.display_label || `${cs.section_no} - ${cs.name} (${cs.section_code})`}
              </option>
            ))}
          </select>

          {/* 3: Category */}
          <select
            value={category}
            disabled={!isCategoryEnabled}
            onChange={(e) => handleCategoryChange(e.target.value)}
            className={`text-xs rounded-lg py-1.5 px-2 truncate transition-colors ${
              isCategoryEnabled
                ? 'border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-600 cursor-pointer font-medium'
                : 'border border-slate-200 bg-slate-100 text-slate-400 cursor-not-allowed select-none'
            }`}
            title={category || (isCategoryEnabled ? 'Step 3: Select Category' : 'Step 3: Disabled (Select CESMM Section first)')}
          >
            <option value="">{isCategoryEnabled ? '3. [Select Category]' : '3. Category (Locked)'}</option>
            {filterOpts?.categories?.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>

          {/* 4: Province */}
          <select
            value={province}
            disabled={!isProvinceEnabled}
            onChange={(e) => handleProvinceChange(e.target.value)}
            className={`text-xs rounded-lg py-1.5 px-2 transition-colors ${
              isProvinceEnabled
                ? 'border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-600 cursor-pointer'
                : 'border border-slate-200 bg-slate-100 text-slate-400 cursor-not-allowed select-none'
            }`}
            title={province || (isProvinceEnabled ? 'Step 4: Select Province' : 'Step 4: Disabled (Select Category first)')}
          >
            <option value="">{isProvinceEnabled ? '4. [Select Province]' : '4. Province (Locked)'}</option>
            {filterOpts?.provinces?.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>

          {/* 5: District */}
          <select
            value={district}
            disabled={!isDistrictEnabled}
            onChange={(e) => handleDistrictChange(e.target.value)}
            className={`text-xs rounded-lg py-1.5 px-2 transition-colors ${
              isDistrictEnabled
                ? 'border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-600 cursor-pointer'
                : 'border border-slate-200 bg-slate-100 text-slate-400 cursor-not-allowed select-none'
            }`}
            title={district || (isDistrictEnabled ? 'Step 5: Select District' : 'Step 5: Disabled (Select Province first)')}
          >
            <option value="">{isDistrictEnabled ? '5. [Select District]' : '5. District (Locked)'}</option>
            {filterOpts?.districts?.map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>

          {/* 6: Year */}
          <select
            value={year}
            disabled={!isYearEnabled}
            onChange={(e) => handleYearChange(e.target.value)}
            className={`text-xs rounded-lg py-1.5 px-2 transition-colors ${
              isYearEnabled
                ? 'border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-600 cursor-pointer'
                : 'border border-slate-200 bg-slate-100 text-slate-400 cursor-not-allowed select-none'
            }`}
            title={year || (isYearEnabled ? 'Step 6: Select Year' : 'Step 6: Disabled (Select District first)')}
          >
            <option value="">{isYearEnabled ? '6. [Select Year]' : '6. Year (Locked)'}</option>
            {filterOpts?.years?.map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>

          {/* 7: Revision */}
          <select
            value={revision}
            disabled={!isRevisionEnabled}
            onChange={(e) => handleRevisionChange(e.target.value)}
            className={`text-xs rounded-lg py-1.5 px-2 transition-colors ${
              isRevisionEnabled
                ? 'border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-600 cursor-pointer'
                : 'border border-slate-200 bg-slate-100 text-slate-400 cursor-not-allowed select-none'
            }`}
            title={revision || (isRevisionEnabled ? 'Step 7: Select Revision' : 'Step 7: Disabled (Select Year first)')}
          >
            <option value="">{isRevisionEnabled ? '7. [Select Revision]' : '7. Revision (Locked)'}</option>
            {filterOpts?.revisions?.map((r) => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>

          {/* 8: VAT */}
          <select
            value={vatBasis}
            disabled={!isVatEnabled}
            onChange={(e) => handleVatChange(e.target.value)}
            className={`text-xs rounded-lg py-1.5 px-2 transition-colors ${
              isVatEnabled
                ? 'border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-600 cursor-pointer'
                : 'border border-slate-200 bg-slate-100 text-slate-400 cursor-not-allowed select-none'
            }`}
            title={vatBasis || (isVatEnabled ? 'Step 8: Select VAT' : 'Step 8: Disabled (Select Revision first)')}
          >
            <option value="">{isVatEnabled ? '8. [Select VAT Basis]' : '8. VAT (Locked)'}</option>
            {filterOpts?.vat_bases?.map((v) => (
              <option key={v} value={v}>{v}</option>
            ))}
          </select>

          {/* 9: Sheets */}
          <select
            value={sheet}
            disabled={!isSheetEnabled}
            onChange={(e) => handleSheetChange(e.target.value)}
            className={`text-xs rounded-lg py-1.5 px-2 truncate transition-colors ${
              isSheetEnabled
                ? 'border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-600 cursor-pointer'
                : 'border border-slate-200 bg-slate-100 text-slate-400 cursor-not-allowed select-none'
            }`}
            title={sheet || (isSheetEnabled ? 'Step 9: Select Sheet' : (!hasSheets && isVatSelected ? 'No sheets exist in this book (N/A)' : 'Step 9: Disabled (Select VAT first)'))}
          >
            <option value="">
              {!isVatSelected
                ? '9. Sheet (Locked)'
                : !hasSheets
                ? '9. Sheet (N/A - None)'
                : '9. [Select Sheet]'}
            </option>
            {filterOpts?.sheets?.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>

          {/* 10: Status */}
          <select
            value={status}
            disabled={!isStatusEnabled}
            onChange={(e) => handleStatusChange(e.target.value)}
            className={`text-xs rounded-lg py-1.5 px-2 transition-colors ${
              isStatusEnabled
                ? 'border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-600 cursor-pointer'
                : 'border border-slate-200 bg-slate-100 text-slate-400 cursor-not-allowed select-none'
            }`}
            title={status || (isStatusEnabled ? 'Step 10: Status' : 'Step 10: Disabled (Complete prior steps)')}
          >
            {!isStatusEnabled ? (
              <option value="ALL">10. Status (Locked)</option>
            ) : (
              <>
                <option value="ALL">10. All Status</option>
                {(filterOpts?.statuses?.length ? filterOpts.statuses : ['VALID', 'APPROVED', 'NEEDS_REVIEW']).map((st) => (
                  <option key={st} value={st}>{st === 'VALID' ? 'Valid' : st === 'APPROVED' ? 'Approved' : st === 'NEEDS_REVIEW' ? 'Needs Review' : st}</option>
                ))}
              </>
            )}
          </select>

          {/* 11: Page # */}
          <input
            type="number"
            min="1"
            disabled={!isPageEnabled}
            placeholder={isPageEnabled ? "11. Page #" : "11. Page (Locked)"}
            value={pageNumber}
            onChange={(e) => { setPageNumber(e.target.value); setPage(1); }}
            className={`text-xs rounded-lg py-1.5 px-2 font-mono w-full transition-colors ${
              isPageEnabled
                ? 'border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-600'
                : 'border border-slate-200 bg-slate-100 text-slate-400 cursor-not-allowed select-none'
            }`}
            title={isPageEnabled ? "Step 11: Direct page quick jump" : "Step 11: Disabled (Select prior steps)"}
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
                onClick={() => {
                  if (onNavigate) {
                    onNavigate('export', { selectedIds: Array.from(selectedIds) });
                  }
                }}
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-700 text-white font-semibold shadow-xs transition-colors cursor-pointer"
                title="Export selected items to Master QS BOQ (.xlsx / PDF)"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Export Master BOQ ({selectedIds.size})</span>
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
                              className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200 hover:bg-indigo-100 hover:border-indigo-300 transition-colors text-left"
                              title={`CESMM-SL Section ${primary.section_no} (${primary.section_code}): ${primary.name || primary.section_name}${primary.is_primary ? ' [Primary]' : ''}${extraCount > 0 ? ` +${extraCount} more` : ''}`}
                            >
                              <Layers className="w-2.5 h-2.5 text-indigo-500 shrink-0" />
                              <span>CESMM {primary.section_no} · Section {primary.section_code}</span>
                              {extraCount > 0 && (
                                <span className="bg-indigo-200 text-indigo-800 rounded px-1 text-[9px] font-bold">
                                  +{extraCount}
                                </span>
                              )}
                            </button>
                          );
                        })()}
                        {(!item.cesmm_sections || item.cesmm_sections.length === 0) && (
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              setCesmmModalItem(item);
                            }}
                            className="opacity-0 group-hover:opacity-100 text-[10px] text-slate-400 hover:text-indigo-600 px-1 py-0.5 border border-dashed border-slate-300 hover:border-indigo-300 rounded transition-all"
                            title="Assign CESMM Section"
                          >
                            + CESMM
                          </button>
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

                    {/* Action Column */}
                    <td className="py-3 px-3 text-center">
                      <div className="flex items-center justify-center gap-1">
                        <button
                          onClick={() => setCesmmModalItem(item)}
                          title="Classify under CESMM-SL Work Sections"
                          className="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-all"
                        >
                          <Layers className="w-4 h-4" />
                        </button>
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
                      </div>
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

      {/* CESMM Classification Modal */}
      {cesmmModalItem && (
        <CESMMMappingModal
          item={cesmmModalItem}
          onClose={() => setCesmmModalItem(null)}
          onUpdated={() => {
            fetchRates();
          }}
        />
      )}
    </div>
  );
};
