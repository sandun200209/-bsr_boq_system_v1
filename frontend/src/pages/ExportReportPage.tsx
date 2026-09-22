import React, { useState, useEffect } from 'react';
import {
  FileSpreadsheet,
  FileText,
  Download,
  CheckCircle,
  AlertTriangle,
  Layers,
  Settings2,
  Eye,
  ShieldCheck,
  Zap,
  Droplets,
  Wind,
  Activity,
  CloudRain,
  Wrench,
  Loader2,
} from 'lucide-react';
import { api } from '../api/client';

interface ExportPackage {
  id: string;
  name: string;
  boq_sheet: string;
  recon_sheet: string;
  default_title: string;
  default_recon_title: string;
  default_note: string;
  columns: string[];
  recon_columns: string[];
}

const PACKAGE_ICONS: Record<string, React.ReactNode> = {
  electrical: <Zap className="w-5 h-5 text-amber-500" />,
  water_supply: <Droplets className="w-5 h-5 text-blue-500" />,
  wastewater: <Wrench className="w-5 h-5 text-slate-500" />,
  rainwater: <CloudRain className="w-5 h-5 text-cyan-500" />,
  mvac: <Wind className="w-5 h-5 text-teal-500" />,
  medical_gas: <Activity className="w-5 h-5 text-rose-500" />,
  all: <Layers className="w-5 h-5 text-indigo-500" />,
};

export const ExportReportPage: React.FC = () => {
  const [packages, setPackages] = useState<ExportPackage[]>([]);
  const [selectedPkgId, setSelectedPkgId] = useState<string>('electrical');
  const [, setLoadingPackages] = useState<boolean>(true);

  // Customization controls
  const [projectTitle, setProjectTitle] = useState<string>('');
  const [sourceNote, setSourceNote] = useState<string>('');
  const [contingencyRate, setContingencyRate] = useState<number>(0.10);
  const [vatStatus, setVatStatus] = useState<string>('Excluded');
  const [showSettings, setShowSettings] = useState<boolean>(false);

  // Preview data
  const [previewData, setPreviewData] = useState<any>(null);
  const [loadingPreview, setLoadingPreview] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'boq' | 'reconciliation'>('boq');

  // Download loading states
  const [downloadingFormat, setDownloadingFormat] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Load packages on mount
  useEffect(() => {
    const fetchPackages = async () => {
      try {
        setLoadingPackages(true);
        const res = await api.getExportPackages();
        setPackages(res.packages);
        if (res.packages.length > 0) {
          const first = res.packages[0];
          setSelectedPkgId(first.id);
          setProjectTitle(first.default_title);
          setSourceNote(first.default_note);
        }
      } catch (err: any) {
        setErrorMessage(err.message || 'Failed to load export packages');
      } finally {
        setLoadingPackages(false);
      }
    };
    fetchPackages();
  }, []);

  // Load preview data whenever selected package changes
  useEffect(() => {
    if (!selectedPkgId) return;
    const loadPreview = async () => {
      try {
        setLoadingPreview(true);
        setErrorMessage(null);
        const data = await api.getExportPreview(selectedPkgId);
        setPreviewData(data);
        setProjectTitle(data.project_title);
        setSourceNote(data.source_note);
      } catch (err: any) {
        setErrorMessage(err.message || 'Failed to load preview data');
      } finally {
        setLoadingPreview(false);
      }
    };
    loadPreview();
  }, [selectedPkgId]);

  const handlePackageChange = (pkgId: string) => {
    setSelectedPkgId(pkgId);
    const p = packages.find((x) => x.id === pkgId);
    if (p) {
      setProjectTitle(p.default_title);
      setSourceNote(p.default_note);
    }
  };

  const handleDownloadExcel = async () => {
    try {
      setDownloadingFormat('excel');
      setErrorMessage(null);
      setSuccessMessage(null);
      await api.downloadExportExcel({
        package_key: selectedPkgId,
        project_title: projectTitle,
        source_note: sourceNote,
        contingency_rate: contingencyRate,
        vat_status: vatStatus,
      });
      setSuccessMessage('Master Excel workbook (.xlsx) downloaded successfully!');
      setTimeout(() => setSuccessMessage(null), 5000);
    } catch (err: any) {
      setErrorMessage(err.message || 'Excel export failed');
    } finally {
      setDownloadingFormat(null);
    }
  };

  const handleDownloadPdf = async (variant: 'combined' | 'boq' | 'reconciliation') => {
    try {
      setDownloadingFormat(`pdf_${variant}`);
      setErrorMessage(null);
      setSuccessMessage(null);
      await api.downloadExportPdf({
        package_key: selectedPkgId,
        variant,
        project_title: projectTitle,
        source_note: sourceNote,
        contingency_rate: contingencyRate,
        vat_status: vatStatus,
      });
      const label =
        variant === 'combined'
          ? 'Combined Executive PDF'
          : variant === 'boq'
          ? 'BOQ Reviewed PDF'
          : 'Reconciliation PDF';
      setSuccessMessage(`${label} downloaded successfully!`);
      setTimeout(() => setSuccessMessage(null), 5000);
    } catch (err: any) {
      setErrorMessage(err.message || 'PDF export failed');
    } finally {
      setDownloadingFormat(null);
    }
  };

  // Compute live preview metrics
  const boqItems: any[] = previewData?.boq_items || [];
  const reconItems: any[] = previewData?.recon_items || [];

  const grossTotal = boqItems.reduce((sum, it) => sum + (it.source_amount || (it.source_qty * it.rate) || 0), 0);
  const dupTotal = boqItems.reduce((sum, it) => sum + (it.duplicate_amount || (it.duplicate_qty * it.rate) || 0), 0);
  const netSubtotal = boqItems.reduce((sum, it) => sum + (it.reviewed_amount || (it.reviewed_qty * it.rate) || (it.source_qty * it.rate) || 0), 0);
  const contingencyAmt = netSubtotal * contingencyRate;
  const estimateTotal = netSubtotal + contingencyAmt;

  const currentPkg = packages.find((p) => p.id === selectedPkgId);

  return (
    <div className="min-h-full bg-slate-50 py-6 px-4 sm:px-6 lg:px-8 space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-teal-950 to-blue-950 rounded-2xl shadow-xl p-6 sm:p-8 text-white relative overflow-hidden">
        <div className="absolute right-0 top-0 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-500/20 border border-teal-400/30 text-teal-300 text-xs font-semibold uppercase tracking-wider">
              <ShieldCheck className="w-4 h-4 text-teal-400" />
              Master Reference Standard: Matara OT Rev 7 Deduplicated
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white flex items-center gap-3">
              <FileSpreadsheet className="w-8 h-8 text-teal-400" />
              QS Engineering Reports & Master Export
            </h1>
            <p className="text-slate-300 text-sm max-w-2xl leading-relaxed">
              Reproduces the exact workbook structure, sheet separation, column order, title layout,
              text wrapping, number formats, and professional QS calculations as the reference workbook.
            </p>
          </div>

          {/* Quick Settings Toggle */}
          <button
            onClick={() => setShowSettings(!showSettings)}
            className={`inline-flex items-center gap-2 px-4 py-2.5 rounded-xl font-medium text-sm transition-all shadow-md ${
              showSettings
                ? 'bg-teal-600 text-white shadow-teal-500/20 ring-2 ring-teal-400'
                : 'bg-white/10 text-white hover:bg-white/20 backdrop-blur-md'
            }`}
          >
            <Settings2 className="w-4 h-4" />
            <span>Customize Report Meta</span>
          </button>
        </div>

        {/* Customization Drawer */}
        {showSettings && (
          <div className="mt-6 pt-6 border-t border-white/10 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 animate-in fade-in duration-200">
            <div className="space-y-1.5 md:col-span-2">
              <label className="text-xs font-semibold text-slate-300">Project Title (Row 1 Merged Banner)</label>
              <input
                type="text"
                value={projectTitle}
                onChange={(e) => setProjectTitle(e.target.value)}
                className="w-full bg-slate-900/80 border border-white/20 rounded-lg px-3 py-2 text-sm text-white focus:ring-2 focus:ring-teal-400 focus:outline-none"
              />
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between">
                <label className="text-xs font-semibold text-slate-300">Contingency Rate</label>
                <span className="text-xs text-teal-300 font-mono font-bold">{(contingencyRate * 100).toFixed(1)}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="0.25"
                step="0.01"
                value={contingencyRate}
                onChange={(e) => setContingencyRate(parseFloat(e.target.value))}
                className="w-full accent-teal-400 cursor-pointer"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300">VAT Basis</label>
              <select
                value={vatStatus}
                onChange={(e) => setVatStatus(e.target.value)}
                className="w-full bg-slate-900/80 border border-white/20 rounded-lg px-3 py-2 text-sm text-white focus:ring-2 focus:ring-teal-400 focus:outline-none"
              >
                <option value="Excluded">Excluded</option>
                <option value="Included (18%)">Included (18%)</option>
                <option value="Exempt">Exempt</option>
              </select>
            </div>

            <div className="space-y-1.5 md:col-span-4">
              <label className="text-xs font-semibold text-slate-300">Source Explanatory Note (Row 2 Merged Box)</label>
              <textarea
                rows={2}
                value={sourceNote}
                onChange={(e) => setSourceNote(e.target.value)}
                className="w-full bg-slate-900/80 border border-white/20 rounded-lg px-3 py-2 text-sm text-white focus:ring-2 focus:ring-teal-400 focus:outline-none"
              />
            </div>
          </div>
        )}
      </div>

      {/* Alerts */}
      {successMessage && (
        <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-4 flex items-center gap-3 text-emerald-800 shadow-sm animate-in fade-in">
          <CheckCircle className="w-5 h-5 text-emerald-600 shrink-0" />
          <p className="text-sm font-medium">{successMessage}</p>
        </div>
      )}

      {errorMessage && (
        <div className="rounded-xl bg-rose-50 border border-rose-200 p-4 flex items-center gap-3 text-rose-800 shadow-sm animate-in fade-in">
          <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0" />
          <p className="text-sm font-medium">{errorMessage}</p>
        </div>
      )}

      {/* Package Selector Bar */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-3">
        <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-thin">
          {packages.map((pkg) => {
            const isSelected = selectedPkgId === pkg.id;
            return (
              <button
                key={pkg.id}
                onClick={() => handlePackageChange(pkg.id)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold whitespace-nowrap transition-all ${
                  isSelected
                    ? 'bg-teal-600 text-white shadow-md shadow-teal-600/20 ring-1 ring-teal-500'
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                }`}
              >
                {PACKAGE_ICONS[pkg.id] || <Layers className="w-4 h-4" />}
                <span>{pkg.name}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Export Options Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Option 1: Excel (.xlsx) */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between group">
          <div className="space-y-3">
            <div className="w-12 h-12 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700">
              <FileSpreadsheet className="w-6 h-6" />
            </div>
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-600">Master Template</span>
              <h3 className="text-base font-bold text-slate-900">Excel (.xlsx)</h3>
              <p className="text-xs text-slate-500 mt-1">
                2 separate worksheets (BOQ Reviewed & Reconciliation) with live formulas, number formats, and exact QS styling.
              </p>
            </div>
          </div>
          <button
            onClick={handleDownloadExcel}
            disabled={downloadingFormat !== null}
            className="mt-4 w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-emerald-600 text-white text-sm font-semibold hover:bg-emerald-700 active:bg-emerald-800 disabled:opacity-50 shadow-sm transition-all"
          >
            {downloadingFormat === 'excel' ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Download className="w-4 h-4" />
            )}
            <span>Export Excel</span>
          </button>
        </div>

        {/* Option 2: Combined PDF */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between group">
          <div className="space-y-3">
            <div className="w-12 h-12 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-700">
              <FileText className="w-6 h-6" />
            </div>
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-blue-600">Full Executive</span>
              <h3 className="text-base font-bold text-slate-900">Combined PDF</h3>
              <p className="text-xs text-slate-500 mt-1">
                Landscape A4 document containing Section 1 (BOQ Reviewed) and Section 2 (Scope Reconciliation).
              </p>
            </div>
          </div>
          <button
            onClick={() => handleDownloadPdf('combined')}
            disabled={downloadingFormat !== null}
            className="mt-4 w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 active:bg-blue-800 disabled:opacity-50 shadow-sm transition-all"
          >
            {downloadingFormat === 'pdf_combined' ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Download className="w-4 h-4" />
            )}
            <span>Export Combined PDF</span>
          </button>
        </div>

        {/* Option 3: BOQ Reviewed PDF */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between group">
          <div className="space-y-3">
            <div className="w-12 h-12 rounded-xl bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-700">
              <FileText className="w-6 h-6" />
            </div>
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-teal-600">Section 1 Only</span>
              <h3 className="text-base font-bold text-slate-900">BOQ Reviewed PDF</h3>
              <p className="text-xs text-slate-500 mt-1">
                Dedicated BOQ line items with deductions, net quantities, and final engineering estimate total.
              </p>
            </div>
          </div>
          <button
            onClick={() => handleDownloadPdf('boq')}
            disabled={downloadingFormat !== null}
            className="mt-4 w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-teal-600 text-white text-sm font-semibold hover:bg-teal-700 active:bg-teal-800 disabled:opacity-50 shadow-sm transition-all"
          >
            {downloadingFormat === 'pdf_boq' ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Download className="w-4 h-4" />
            )}
            <span>Export BOQ PDF</span>
          </button>
        </div>

        {/* Option 4: Reconciliation PDF */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between group">
          <div className="space-y-3">
            <div className="w-12 h-12 rounded-xl bg-indigo-50 border border-indigo-200 flex items-center justify-center text-indigo-700">
              <FileText className="w-6 h-6" />
            </div>
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-600">Section 2 Only</span>
              <h3 className="text-base font-bold text-slate-900">Reconciliation PDF</h3>
              <p className="text-xs text-slate-500 mt-1">
                Scope boundary matrix detailing interfaces, duplication risks, and tender actions.
              </p>
            </div>
          </div>
          <button
            onClick={() => handleDownloadPdf('reconciliation')}
            disabled={downloadingFormat !== null}
            className="mt-4 w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-700 active:bg-indigo-800 disabled:opacity-50 shadow-sm transition-all"
          >
            {downloadingFormat === 'pdf_reconciliation' ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Download className="w-4 h-4" />
            )}
            <span>Export Recon PDF</span>
          </button>
        </div>
      </div>

      {/* KPI Financial Summary Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
          <div className="text-xs text-slate-500 font-medium">Source BOQ Gross</div>
          <div className="text-base sm:text-lg font-bold text-slate-900 font-mono mt-1">
            LKR {grossTotal.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>

        <div className="bg-white rounded-xl p-4 border border-rose-200 shadow-sm bg-rose-50/30">
          <div className="text-xs text-rose-600 font-medium">Duplicate Deductions</div>
          <div className="text-base sm:text-lg font-bold text-rose-700 font-mono mt-1">
            - LKR {dupTotal.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>

        <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
          <div className="text-xs text-slate-500 font-medium">Reviewed Direct Net</div>
          <div className="text-base sm:text-lg font-bold text-teal-700 font-mono mt-1">
            LKR {netSubtotal.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>

        <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
          <div className="text-xs text-slate-500 font-medium">Contingency ({(contingencyRate * 100).toFixed(1)}%)</div>
          <div className="text-base sm:text-lg font-bold text-slate-800 font-mono mt-1">
            LKR {contingencyAmt.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>

        <div className="bg-white rounded-xl p-4 border border-blue-300 shadow-sm bg-blue-50/40 col-span-2 md:col-span-1">
          <div className="text-xs text-blue-700 font-medium">Engineer's Estimate (excl. VAT)</div>
          <div className="text-base sm:text-lg font-extrabold text-blue-900 font-mono mt-1">
            LKR {estimateTotal.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>
      </div>

      {/* Live Data Preview Section */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {/* Table View Tabs */}
        <div className="border-b border-slate-200 px-6 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-50/50">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab('boq')}
              className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                activeTab === 'boq'
                  ? 'bg-teal-600 text-white shadow-sm'
                  : 'text-slate-600 hover:bg-slate-200/60'
              }`}
            >
              Sheet 1: {currentPkg?.boq_sheet || 'BOQ Reviewed'} ({boqItems.length})
            </button>
            <button
              onClick={() => setActiveTab('reconciliation')}
              className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                activeTab === 'reconciliation'
                  ? 'bg-teal-600 text-white shadow-sm'
                  : 'text-slate-600 hover:bg-slate-200/60'
              }`}
            >
              Sheet 2: {currentPkg?.recon_sheet || 'Reconciliation'} ({reconItems.length})
            </button>
          </div>

          <div className="text-xs text-slate-500 flex items-center gap-1.5 font-medium">
            <Eye className="w-4 h-4 text-slate-400" />
            Live Preview (Exact columns and order reproduced)
          </div>
        </div>

        {/* Loading Spinner */}
        {loadingPreview ? (
          <div className="p-16 flex flex-col items-center justify-center text-slate-400 space-y-3">
            <Loader2 className="w-8 h-8 animate-spin text-teal-600" />
            <p className="text-sm font-medium">Loading package preview from master template...</p>
          </div>
        ) : activeTab === 'boq' ? (
          /* BOQ Reviewed Table Preview */
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700 border-collapse">
              <thead>
                <tr className="bg-[#5B9BD5] text-white font-bold text-[11px] border-b border-slate-300">
                  <th className="p-2.5 text-center whitespace-nowrap">Source Row</th>
                  <th className="p-2.5 text-center whitespace-nowrap">Item</th>
                  <th className="p-2.5 min-w-[280px]">Description</th>
                  <th className="p-2.5 text-center whitespace-nowrap">Unit</th>
                  <th className="p-2.5 text-right whitespace-nowrap">Source Qty</th>
                  <th className="p-2.5 text-right whitespace-nowrap">Rate (LKR)</th>
                  <th className="p-2.5 text-right whitespace-nowrap">Source Amount</th>
                  <th className="p-2.5 text-right whitespace-nowrap">Duplicate Qty</th>
                  <th className="p-2.5 text-right whitespace-nowrap">Duplicate Amount</th>
                  <th className="p-2.5 text-right whitespace-nowrap">Reviewed Qty</th>
                  <th className="p-2.5 text-right whitespace-nowrap">Reviewed Amount</th>
                  <th className="p-2.5 min-w-[220px]">Overlap / Reason</th>
                  <th className="p-2.5 text-center whitespace-nowrap">Action</th>
                  <th className="p-2.5 text-center whitespace-nowrap">Confidence</th>
                  <th className="p-2.5 min-w-[180px]">Remarks</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {boqItems.map((row, idx) => {
                  const srcAmt = row.source_amount || row.source_qty * row.rate || 0;
                  const dupAmt = row.duplicate_amount || row.duplicate_qty * row.rate || 0;
                  const revAmt = row.reviewed_amount || row.reviewed_qty * row.rate || 0;
                  const hasDup = row.duplicate_qty > 0;

                  return (
                    <tr
                      key={idx}
                      className={`hover:bg-slate-50 transition-colors ${
                        hasDup ? 'bg-amber-50/20' : idx % 2 === 1 ? 'bg-slate-50/50' : 'bg-white'
                      }`}
                    >
                      <td className="p-2.5 text-center font-mono text-slate-500">{row.source_row || idx + 1}</td>
                      <td className="p-2.5 text-center font-mono font-medium text-slate-900">{row.item || '-'}</td>
                      <td className="p-2.5 text-slate-900 leading-relaxed">{row.description}</td>
                      <td className="p-2.5 text-center text-slate-600 font-medium">{row.unit}</td>
                      <td className="p-2.5 text-right font-mono">{Number(row.source_qty).toFixed(2)}</td>
                      <td className="p-2.5 text-right font-mono font-medium">{Number(row.rate).toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                      <td className="p-2.5 text-right font-mono text-slate-700">{srcAmt.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                      <td className={`p-2.5 text-right font-mono ${hasDup ? 'text-rose-600 font-bold' : 'text-slate-400'}`}>
                        {Number(row.duplicate_qty).toFixed(2)}
                      </td>
                      <td className={`p-2.5 text-right font-mono ${hasDup ? 'text-rose-600 font-bold' : 'text-slate-400'}`}>
                        {dupAmt > 0 ? `- ${dupAmt.toLocaleString('en-US', { minimumFractionDigits: 2 })}` : '0.00'}
                      </td>
                      <td className="p-2.5 text-right font-mono font-bold text-teal-700">{Number(row.reviewed_qty).toFixed(2)}</td>
                      <td className="p-2.5 text-right font-mono font-bold text-teal-700">{revAmt.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                      <td className="p-2.5 text-slate-600 text-[11px] leading-relaxed italic">{row.overlap_reason || '-'}</td>
                      <td className="p-2.5 text-center">
                        <span
                          className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                            row.action === 'REDUCE'
                              ? 'bg-amber-100 text-amber-800'
                              : row.action === 'DEDUCT'
                              ? 'bg-rose-100 text-rose-800'
                              : 'bg-emerald-100 text-emerald-800'
                          }`}
                        >
                          {row.action || 'RETAIN'}
                        </span>
                      </td>
                      <td className="p-2.5 text-center text-slate-600 text-[11px]">{row.confidence || 'High'}</td>
                      <td className="p-2.5 text-slate-500 text-[11px]">{row.remarks || '-'}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          /* Scope Reconciliation Table Preview */
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700 border-collapse">
              <thead>
                <tr className="bg-[#5B9BD5] text-white font-bold text-[11px] border-b border-slate-300">
                  <th className="p-2.5 min-w-[160px]">Scope Element</th>
                  <th className="p-2.5 min-w-[160px]">Source BOQ</th>
                  <th className="p-2.5 min-w-[170px]">Other Package</th>
                  <th className="p-2.5 min-w-[160px]">Consolidated Treatment</th>
                  <th className="p-2.5 min-w-[130px]">Deduction / Adjustment</th>
                  <th className="p-2.5 min-w-[160px]">Reason</th>
                  <th className="p-2.5 text-center min-w-[90px]">Risk</th>
                  <th className="p-2.5 min-w-[200px]">Tender Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {reconItems.map((r, idx) => (
                  <tr key={idx} className={idx % 2 === 1 ? 'bg-slate-50/50' : 'bg-white'}>
                    <td className="p-2.5 font-semibold text-slate-900">{r[0]}</td>
                    <td className="p-2.5 text-slate-700">{r[1]}</td>
                    <td className="p-2.5 text-slate-700">{r[2]}</td>
                    <td className="p-2.5 text-teal-800 font-medium">{r[3]}</td>
                    <td className="p-2.5 font-mono text-rose-600 font-semibold">{r[4]}</td>
                    <td className="p-2.5 text-slate-600 leading-relaxed">{r[5]}</td>
                    <td className="p-2.5 text-center">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold ${
                          String(r[6]).toLowerCase().includes('high')
                            ? 'bg-rose-100 text-rose-800'
                            : 'bg-amber-100 text-amber-800'
                        }`}
                      >
                        {r[6]}
                      </span>
                    </td>
                    <td className="p-2.5 text-slate-700 leading-relaxed font-medium">{r[7]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
