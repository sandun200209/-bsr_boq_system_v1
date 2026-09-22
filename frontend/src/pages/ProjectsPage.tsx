import React, { useState, useEffect } from 'react';
import {
  FolderKanban,
  Plus,
  FileSpreadsheet,
  Download,
  Calendar,
  Search,
  CheckCircle2,
  Sliders,
  DollarSign,
  Building,
  RefreshCw,
  X,
  SlidersHorizontal,
  Loader2,
} from 'lucide-react';
import { api } from '../api/client';

export const ProjectsPage: React.FC = () => {
  const [projects, setProjects] = useState<any[]>([]);
  const [selectedProject, setSelectedProject] = useState<any | null>(null);
  const [activeSectionId, setActiveSectionId] = useState<number | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [exporting, setExporting] = useState<boolean>(false);

  // Modals
  const [showRateModal, setShowRateModal] = useState<boolean>(false);
  const [showAddSectionModal, setShowAddSectionModal] = useState<boolean>(false);
  const [showNewProjectModal, setShowNewProjectModal] = useState<boolean>(false);
  const [showTemplateModal, setShowTemplateModal] = useState<boolean>(false);
  const [templates, setTemplates] = useState<any[]>([]);

  // Historical Rate Comparison state
  const [rateSearchQuery, setRateSearchQuery] = useState<string>('brickwork');
  const [histComparison, setHistComparison] = useState<any | null>(null);
  const [histLoading, setHistLoading] = useState<boolean>(false);
  const [selectedHistRate, setSelectedHistRate] = useState<any | null>(null);
  const [itemQty, setItemQty] = useState<number>(1.0);
  const [itemAdjustment, setItemAdjustment] = useState<number>(0.0);
  const [itemJustification, setItemJustification] = useState<string>('');
  const [itemRemarks, setItemRemarks] = useState<string>('');

  // Duplication Record Add Form
  const [newDupItem, setNewDupItem] = useState({
    item: '',
    bsr_ref: '',
    description: '',
    unit: 'Item',
    qty: 1,
    rate: 0,
    rate_source_year: '2026',
    duplicate_with: '',
    status: 'RETAIN',
    remarks: '',
  });

  // Change Register Add Form
  const [newChangeItem, setNewChangeItem] = useState({
    ref_code: '',
    package_sheet: 'Electrical',
    item_code: '',
    description: '',
    original_status: '',
    rev7_action: '',
    duplicate_with: '',
    rate_source: 'BSR 2026',
    cost_impact: 0,
    reason: '',
  });

  // New Project Form
  const [newProjData, setNewProjData] = useState({
    project_code: '',
    project_name: '',
    project_base_year: 2026,
    location: 'District General Hospital Matara',
    description: '',
    contingency_rate: 0.10,
  });

  // New Section Form
  const [newSecData, setNewSecData] = useState({
    section_code: '',
    section_name: '',
    section_type: 'BOQ',
    target_sheet: '',
  });

  // Load projects
  const fetchProjects = async (selectId?: number) => {
    setLoading(true);
    try {
      const data = await api.getProjects();
      setProjects(data);
      if (data.length > 0) {
        const cur = selectId ? data.find((p) => p.id === selectId) || data[0] : data[0];
        setSelectedProject(cur);
        if (cur.sections && cur.sections.length > 0) {
          setActiveSectionId((prev) => (prev ? prev : cur.sections[0].id));
        }
      }
    } catch (err) {
      console.error('Failed to load projects:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  // Fetch templates
  const loadTemplates = async () => {
    try {
      const res = await api.getSystemTemplates();
      setTemplates(res);
    } catch (e) {
      console.error('Failed to load templates:', e);
    }
  };

  // Run historical rate search
  const runHistoricalSearch = async (queryText?: string) => {
    const q = queryText !== undefined ? queryText : rateSearchQuery;
    if (!q.trim()) return;
    setHistLoading(true);
    try {
      const res = await api.getHistoricalRateComparison({
        query: q.trim(),
        base_year: selectedProject?.project_base_year || 2026,
      });
      setHistComparison(res);
      setSelectedHistRate(null);
    } catch (err) {
      console.error('Historical rate search failed:', err);
    } finally {
      setHistLoading(false);
    }
  };

  // Add Item to active BOQ section
  const handleAddProjectItem = async () => {
    if (!selectedProject || !activeSectionId || !selectedHistRate) return;
    try {
      const rateVal = selectedHistRate.rate;
      const adjVal = itemAdjustment || 0;
      const computedAmt = itemQty * (rateVal + adjVal);

      await api.addProjectItem(activeSectionId, {
        item_no: selectedHistRate.item_code,
        description: selectedHistRate.description,
        unit: selectedHistRate.unit,
        quantity: itemQty,
        selected_rate: rateVal,
        rate_source_year: String(selectedHistRate.year), // Explicit separate rate source year
        rate_source_book: selectedHistRate.book_title,
        rate_source_item_code: selectedHistRate.item_code,
        adjustment: adjVal,
        rate_justification: itemJustification || `Adopted from ${selectedHistRate.year} BSR with ${adjVal} LKR adjustment`,
        amount: computedAmt,
        remarks: itemRemarks,
        sort_order: (currentSection?.items?.length || 0) + 1,
      });

      setShowRateModal(false);
      setSelectedHistRate(null);
      setItemAdjustment(0);
      setItemJustification('');
      setItemRemarks('');
      await fetchProjects(selectedProject.id);
    } catch (err) {
      alert('Failed to add rate item to section.');
    }
  };

  // Add Duplication Record
  const handleAddDuplicationRecord = async () => {
    if (!activeSectionId || !newDupItem.description.trim()) return;
    try {
      await api.addDuplicationRecord(activeSectionId, newDupItem);
      setNewDupItem({
        item: '',
        bsr_ref: '',
        description: '',
        unit: 'Item',
        qty: 1,
        rate: 0,
        rate_source_year: String(selectedProject?.project_base_year || 2026),
        duplicate_with: '',
        status: 'RETAIN',
        remarks: '',
      });
      await fetchProjects(selectedProject.id);
    } catch (e) {
      alert('Failed to add duplication review record.');
    }
  };

  // Add Change Register Record
  const handleAddChangeRecord = async () => {
    if (!activeSectionId || !newChangeItem.description.trim()) return;
    try {
      await api.addChangeRegisterRecord(activeSectionId, newChangeItem);
      setNewChangeItem({
        ref_code: '',
        package_sheet: 'Electrical',
        item_code: '',
        description: '',
        original_status: '',
        rev7_action: '',
        duplicate_with: '',
        rate_source: 'BSR 2026',
        cost_impact: 0,
        reason: '',
      });
      await fetchProjects(selectedProject.id);
    } catch (e) {
      alert('Failed to add change register record.');
    }
  };

  // Create New Project
  const handleCreateProject = async () => {
    if (!newProjData.project_code.trim() || !newProjData.project_name.trim()) {
      alert('Please provide project code and name.');
      return;
    }
    try {
      const res = await api.createProject(newProjData);
      setShowNewProjectModal(false);
      await fetchProjects(res.id);
    } catch (e: any) {
      alert(e.message || 'Failed to create project.');
    }
  };

  // Add Section
  const handleCreateSection = async () => {
    if (!selectedProject || !newSecData.section_name.trim()) return;
    try {
      const res = await api.addProjectSection(selectedProject.id, {
        section_code: newSecData.section_code.trim() || `SEC-${Date.now().toString().slice(-4)}`,
        section_name: newSecData.section_name.trim(),
        section_type: newSecData.section_type,
        target_sheet: newSecData.target_sheet.trim() || undefined,
        sort_order: (selectedProject.sections?.length || 0) + 1,
      });
      setShowAddSectionModal(false);
      await fetchProjects(selectedProject.id);
      setActiveSectionId(res.id);
    } catch (e) {
      alert('Failed to create section.');
    }
  };

  // Export handlers
  const handleExportConsolidated = async () => {
    if (!selectedProject) return;
    setExporting(true);
    try {
      await api.downloadProjectExcel(selectedProject.id, 'consolidated');
    } catch (e) {
      alert('Consolidated export failed.');
    } finally {
      setExporting(false);
    }
  };

  const handleExportCurrentSection = async () => {
    if (!selectedProject || !activeSectionId) return;
    setExporting(true);
    try {
      await api.downloadProjectExcel(selectedProject.id, 'separate', activeSectionId);
    } catch (e) {
      alert('Separate section export failed.');
    } finally {
      setExporting(false);
    }
  };

  const currentSection = selectedProject?.sections?.find((s: any) => s.id === activeSectionId);

  if (loading && projects.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-[1600px] mx-auto space-y-6">
      {/* Top Bar: Project Selector & New Project */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-blue-600 text-white rounded-lg shadow-sm">
            <FolderKanban className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-slate-900">
                {selectedProject?.project_name || 'Project Estimating Hub'}
              </h1>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-100 text-blue-800 border border-blue-200">
                {selectedProject?.project_code}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Multi-Year Rate Selection • Section Scope Classification • Duplication & Change Register • Template Engine
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <select
            value={selectedProject?.id || ''}
            onChange={(e) => {
              const p = projects.find((x) => x.id === Number(e.target.value));
              if (p) {
                setSelectedProject(p);
                if (p.sections && p.sections.length > 0) {
                  setActiveSectionId(p.sections[0].id);
                }
              }
            }}
            className="text-xs font-semibold px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:border-blue-500 text-slate-700"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.project_code} - {p.project_name}
              </option>
            ))}
          </select>

          <button
            onClick={() => setShowNewProjectModal(true)}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs transition-colors shadow-xs"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Project</span>
          </button>

          <button
            onClick={() => {
              loadTemplates();
              setShowTemplateModal(true);
            }}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 font-semibold text-xs transition-colors"
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
            <span>Templates</span>
          </button>
        </div>
      </div>

      {/* Project Meta & Rule Indicator Card */}
      {selectedProject && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex items-center gap-3">
            <div className="p-3 bg-amber-50 rounded-lg text-amber-600 border border-amber-200">
              <Calendar className="w-5 h-5" />
            </div>
            <div>
              <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Project Base Year</div>
              <div className="text-xl font-extrabold text-slate-900">{selectedProject.project_base_year}</div>
              <div className="text-[10px] text-amber-700 font-medium">Distinct from Rate Source Years</div>
            </div>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex items-center gap-3">
            <div className="p-3 bg-emerald-50 rounded-lg text-emerald-600 border border-emerald-200">
              <Building className="w-5 h-5" />
            </div>
            <div>
              <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Project Location</div>
              <div className="text-sm font-bold text-slate-800 truncate">{selectedProject.location}</div>
              <div className="text-[10px] text-slate-500">Status: {selectedProject.status}</div>
            </div>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex items-center gap-3">
            <div className="p-3 bg-blue-50 rounded-lg text-blue-600 border border-blue-200">
              <Sliders className="w-5 h-5" />
            </div>
            <div>
              <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Contingency & VAT</div>
              <div className="text-sm font-bold text-slate-800">
                {(selectedProject.contingency_rate * 100).toFixed(0)}% Contingency
              </div>
              <div className="text-[10px] text-slate-500">VAT: {selectedProject.vat_status}</div>
            </div>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex items-center gap-3">
            <div className="p-3 bg-teal-50 rounded-lg text-teal-600 border border-teal-200">
              <DollarSign className="w-5 h-5" />
            </div>
            <div>
              <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Total Est. (incl. 10%)</div>
              <div className="text-lg font-black text-teal-700 font-mono">
                LKR {Number(selectedProject.total_estimate || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </div>
              <div className="text-[10px] text-teal-600">{selectedProject.sections?.length || 0} Sections Classified</div>
            </div>
          </div>
        </div>
      )}

      {/* Main Workspace: Sections & Data Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        {/* Section Tabs Header */}
        <div className="p-3 bg-slate-50 border-b border-slate-200 flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap items-center gap-1.5 overflow-x-auto">
            {selectedProject?.sections?.map((sec: any) => {
              const isSelected = sec.id === activeSectionId;
              let badgeColor = 'bg-slate-200 text-slate-700';
              if (sec.section_type === 'DUPLICATION') badgeColor = 'bg-rose-100 text-rose-800 border-rose-300';
              if (sec.section_type === 'CHANGE_REGISTER') badgeColor = 'bg-purple-100 text-purple-800 border-purple-300';
              if (sec.section_type === 'RECONCILIATION') badgeColor = 'bg-teal-100 text-teal-800 border-teal-300';

              return (
                <button
                  key={sec.id}
                  onClick={() => setActiveSectionId(sec.id)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-2 border transition-all ${
                    isSelected
                      ? 'bg-blue-600 text-white border-blue-600 shadow-xs'
                      : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-100'
                  }`}
                >
                  <span>{sec.section_name}</span>
                  <span
                    className={`px-1.5 py-0.2 rounded text-[10px] font-bold ${
                      isSelected ? 'bg-blue-800 text-blue-100' : badgeColor
                    }`}
                  >
                    {sec.section_type}
                  </span>
                </button>
              );
            })}

            <button
              onClick={() => setShowAddSectionModal(true)}
              className="px-2.5 py-1.5 rounded-lg text-xs font-semibold text-blue-600 hover:bg-blue-50 border border-dashed border-blue-300 flex items-center gap-1"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Section</span>
            </button>
          </div>

          {/* Export Actions for Active Project */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleExportCurrentSection}
              disabled={exporting}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-slate-300 hover:bg-slate-100 text-slate-800 font-semibold text-xs transition-colors cursor-pointer shadow-xs disabled:opacity-50"
              title="Export Option B: Separate Excel file for this active section only"
            >
              <FileSpreadsheet className="w-3.5 h-3.5 text-blue-600" />
              <span>Export Section (.xlsx)</span>
            </button>

            <button
              onClick={handleExportConsolidated}
              disabled={exporting}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs transition-colors cursor-pointer shadow-sm disabled:opacity-50"
              title="Export Option A: One Excel workbook with each section as a separate worksheet"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export Master Workbook (All Sections)</span>
            </button>
          </div>
        </div>

        {/* Active Section Content */}
        {currentSection && (
          <div className="p-4 space-y-4">
            {/* Section Banner */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3 bg-blue-50/50 border border-blue-100 rounded-lg text-xs">
              <div>
                <span className="font-bold text-blue-900 text-sm">{currentSection.section_name}</span>
                <span className="ml-2 text-slate-500 font-mono">[{currentSection.section_code}]</span>
                <p className="text-slate-600 mt-0.5">
                  Target Worksheet: <span className="font-semibold text-blue-800">{currentSection.target_sheet || 'Auto-mapped'}</span>
                </p>
              </div>

              {currentSection.section_type === 'BOQ' && (
                <button
                  onClick={() => {
                    setShowRateModal(true);
                    runHistoricalSearch(rateSearchQuery);
                  }}
                  className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-xs"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add Item via Historical Rate Comparison</span>
                </button>
              )}
            </div>

            {/* Render Data Table according to Section Type */}
            {currentSection.section_type === 'BOQ' && (
              /* Standard BOQ Section Items */
              <div className="overflow-x-auto border border-slate-200 rounded-lg">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-[#5B9BD5] text-white font-bold text-[11px]">
                      <th className="p-2.5 text-center w-12">Item</th>
                      <th className="p-2.5 min-w-[240px]">Description</th>
                      <th className="p-2.5 text-center w-16">Unit</th>
                      <th className="p-2.5 text-right w-20">Qty</th>
                      <th className="p-2.5 text-right w-28">Rate (LKR)</th>
                      <th className="p-2.5 text-center w-28 bg-blue-700/80">Rate Source Year</th>
                      <th className="p-2.5 min-w-[150px]">Rate Source Book</th>
                      <th className="p-2.5 text-right w-24">Adjustment</th>
                      <th className="p-2.5 text-right w-28">Amount (LKR)</th>
                      <th className="p-2.5 min-w-[180px]">Rate Justification</th>
                      <th className="p-2.5 min-w-[150px]">Remarks</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 bg-white">
                    {currentSection.items?.length === 0 ? (
                      <tr>
                        <td colSpan={11} className="p-8 text-center text-slate-400">
                          No items in this section. Click <b>"Add Item via Historical Rate Comparison"</b> to select rates across years.
                        </td>
                      </tr>
                    ) : (
                      currentSection.items?.map((it: any, idx: number) => (
                        <tr key={it.id} className="hover:bg-blue-50/20">
                          <td className="p-2.5 text-center font-semibold text-slate-600">{it.item_no || idx + 1}</td>
                          <td className="p-2.5 font-medium text-slate-900">{it.description}</td>
                          <td className="p-2.5 text-center text-slate-600">{it.unit}</td>
                          <td className="p-2.5 text-right font-mono">{Number(it.quantity).toFixed(2)}</td>
                          <td className="p-2.5 text-right font-mono font-medium text-slate-900">
                            {Number(it.selected_rate).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                          </td>
                          <td className="p-2.5 text-center">
                            <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-amber-100 text-amber-900 border border-amber-300">
                              BSR {it.rate_source_year}
                            </span>
                          </td>
                          <td className="p-2.5 text-slate-600 truncate max-w-[180px]" title={it.rate_source_book}>
                            {it.rate_source_book || '-'}
                          </td>
                          <td className="p-2.5 text-right font-mono text-slate-700">{it.adjustment || 0}</td>
                          <td className="p-2.5 text-right font-mono font-bold text-slate-900">
                            {Number(it.amount).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                          </td>
                          <td className="p-2.5 text-slate-600 leading-relaxed text-[11px]">{it.rate_justification || '-'}</td>
                          <td className="p-2.5 text-slate-500 text-[11px]">{it.remarks || '-'}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {/* DUPLICATION REVIEW VIEW: Exact OT Site Works Columns */}
            {currentSection.section_type === 'DUPLICATION' && (
              <div className="space-y-3">
                <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-800 flex items-center justify-between">
                  <div>
                    <b>Target Sheet: MATARA OT RENOVATION – SITE WORKS BOQ REVIEWED FOR DUPLICATION</b>
                    <p className="text-[11px] text-rose-700 mt-0.5">
                      Maintains separate BOQ fields with Duplicate With & Review Status columns. Never combined with Change Register.
                    </p>
                  </div>
                </div>

                <div className="overflow-x-auto border border-slate-200 rounded-lg">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="bg-[#5B9BD5] text-white font-bold text-[11px]">
                        <th className="p-2 text-center w-12">Item</th>
                        <th className="p-2 w-28">BSR Ref</th>
                        <th className="p-2 min-w-[220px]">Description</th>
                        <th className="p-2 text-center w-16">Unit</th>
                        <th className="p-2 text-right w-20">Qty</th>
                        <th className="p-2 text-right w-28">Rate (LKR)</th>
                        <th className="p-2 text-right w-28">Amount (LKR)</th>
                        <th className="p-2 text-center w-28 bg-rose-800/60">Rate Source Year</th>
                        <th className="p-2 min-w-[160px]">Duplicate With</th>
                        <th className="p-2 text-center w-24">Status</th>
                        <th className="p-2 min-w-[180px]">Remarks</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200 bg-white">
                      {currentSection.duplication_records?.map((d: any) => (
                        <tr key={d.id} className="hover:bg-rose-50/20">
                          <td className="p-2 text-center font-bold text-slate-700">{d.item}</td>
                          <td className="p-2 font-mono text-slate-600">{d.bsr_ref || '-'}</td>
                          <td className="p-2 font-medium text-slate-900">{d.description}</td>
                          <td className="p-2 text-center text-slate-600">{d.unit}</td>
                          <td className="p-2 text-right font-mono">{d.qty}</td>
                          <td className="p-2 text-right font-mono">{Number(d.rate).toLocaleString()}</td>
                          <td className="p-2 text-right font-mono font-bold text-slate-900">
                            {Number(d.amount).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                          </td>
                          <td className="p-2 text-center font-bold text-amber-800">{d.rate_source_year}</td>
                          <td className="p-2 text-rose-700 font-medium">{d.duplicate_with || 'None'}</td>
                          <td className="p-2 text-center">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                d.status === 'RETAIN'
                                  ? 'bg-emerald-100 text-emerald-800'
                                  : d.status === 'REDUCE'
                                  ? 'bg-amber-100 text-amber-800'
                                  : 'bg-rose-100 text-rose-800'
                              }`}
                            >
                              {d.status}
                            </span>
                          </td>
                          <td className="p-2 text-slate-600 text-[11px]">{d.remarks || '-'}</td>
                        </tr>
                      ))}

                      {/* Inline Add Row */}
                      <tr className="bg-slate-50 border-t-2 border-slate-300">
                        <td className="p-2">
                          <input
                            type="text"
                            placeholder="#"
                            value={newDupItem.item}
                            onChange={(e) => setNewDupItem({ ...newDupItem, item: e.target.value })}
                            className="w-full text-xs p-1 rounded border border-slate-300"
                          />
                        </td>
                        <td className="p-2">
                          <input
                            type="text"
                            placeholder="BSR Ref"
                            value={newDupItem.bsr_ref}
                            onChange={(e) => setNewDupItem({ ...newDupItem, bsr_ref: e.target.value })}
                            className="w-full text-xs p-1 rounded border border-slate-300"
                          />
                        </td>
                        <td className="p-2">
                          <input
                            type="text"
                            placeholder="Description..."
                            value={newDupItem.description}
                            onChange={(e) => setNewDupItem({ ...newDupItem, description: e.target.value })}
                            className="w-full text-xs p-1 rounded border border-slate-300"
                          />
                        </td>
                        <td className="p-2">
                          <input
                            type="text"
                            placeholder="Unit"
                            value={newDupItem.unit}
                            onChange={(e) => setNewDupItem({ ...newDupItem, unit: e.target.value })}
                            className="w-full text-xs p-1 rounded border border-slate-300 text-center"
                          />
                        </td>
                        <td className="p-2">
                          <input
                            type="number"
                            placeholder="Qty"
                            value={newDupItem.qty}
                            onChange={(e) => setNewDupItem({ ...newDupItem, qty: parseFloat(e.target.value) || 0 })}
                            className="w-full text-xs p-1 rounded border border-slate-300 text-right"
                          />
                        </td>
                        <td className="p-2">
                          <input
                            type="number"
                            placeholder="Rate"
                            value={newDupItem.rate}
                            onChange={(e) => setNewDupItem({ ...newDupItem, rate: parseFloat(e.target.value) || 0 })}
                            className="w-full text-xs p-1 rounded border border-slate-300 text-right"
                          />
                        </td>
                        <td className="p-2 text-right font-mono font-bold text-slate-700">
                          {(newDupItem.qty * newDupItem.rate).toLocaleString()}
                        </td>
                        <td className="p-2">
                          <input
                            type="text"
                            placeholder="Year"
                            value={newDupItem.rate_source_year}
                            onChange={(e) => setNewDupItem({ ...newDupItem, rate_source_year: e.target.value })}
                            className="w-full text-xs p-1 rounded border border-slate-300 text-center font-bold"
                          />
                        </td>
                        <td className="p-2">
                          <input
                            type="text"
                            placeholder="Duplicate with..."
                            value={newDupItem.duplicate_with}
                            onChange={(e) => setNewDupItem({ ...newDupItem, duplicate_with: e.target.value })}
                            className="w-full text-xs p-1 rounded border border-slate-300"
                          />
                        </td>
                        <td className="p-2">
                          <select
                            value={newDupItem.status}
                            onChange={(e) => setNewDupItem({ ...newDupItem, status: e.target.value })}
                            className="w-full text-xs p-1 rounded border border-slate-300 font-semibold"
                          >
                            <option value="RETAIN">RETAIN</option>
                            <option value="REDUCE">REDUCE</option>
                            <option value="DEDUCT">DEDUCT</option>
                            <option value="REVIEW">REVIEW</option>
                          </select>
                        </td>
                        <td className="p-2 flex items-center gap-2">
                          <input
                            type="text"
                            placeholder="Remarks"
                            value={newDupItem.remarks}
                            onChange={(e) => setNewDupItem({ ...newDupItem, remarks: e.target.value })}
                            className="w-full text-xs p-1 rounded border border-slate-300"
                          />
                          <button
                            onClick={handleAddDuplicationRecord}
                            className="px-2.5 py-1 bg-rose-600 text-white rounded hover:bg-rose-700 font-bold"
                          >
                            Add
                          </button>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* CHANGE REGISTER VIEW: Exact REV 7 Change Register Columns */}
            {currentSection.section_type === 'CHANGE_REGISTER' && (
              <div className="space-y-3">
                <div className="p-3 bg-purple-50 border border-purple-200 rounded-lg text-xs text-purple-900 flex items-center justify-between">
                  <div>
                    <b>Target Sheet: REV 7 CONSOLIDATION CHANGE / DUPLICATION REGISTER</b>
                    <p className="text-[11px] text-purple-700 mt-0.5">
                      Maintains multi-package change audit history with cost impact and follow-up reasons. Never mixed with Site Works.
                    </p>
                  </div>
                </div>

                <div className="overflow-x-auto border border-slate-200 rounded-lg">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="bg-[#5B9BD5] text-white font-bold text-[11px]">
                        <th className="p-2 text-center w-20">Ref</th>
                        <th className="p-2 w-28">Package / Sheet</th>
                        <th className="p-2 w-24">Item</th>
                        <th className="p-2 min-w-[240px]">Description</th>
                        <th className="p-2 min-w-[140px]">Original Status</th>
                        <th className="p-2 min-w-[150px]">REV 7 Action</th>
                        <th className="p-2 min-w-[150px]">Duplicate With</th>
                        <th className="p-2 text-center w-24">Rate Source</th>
                        <th className="p-2 text-right w-28">Cost Impact</th>
                        <th className="p-2 min-w-[180px]">Reason</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200 bg-white">
                      {currentSection.change_register_records?.map((c: any) => (
                        <tr key={c.id} className="hover:bg-purple-50/20">
                          <td className="p-2 text-center font-bold text-purple-900">{c.ref_code}</td>
                          <td className="p-2 font-semibold text-slate-800">{c.package_sheet}</td>
                          <td className="p-2 font-mono text-slate-600">{c.item_code || '-'}</td>
                          <td className="p-2 font-medium text-slate-900">{c.description}</td>
                          <td className="p-2 text-slate-600 text-[11px]">{c.original_status || '-'}</td>
                          <td className="p-2 text-blue-800 font-semibold">{c.rev7_action || '-'}</td>
                          <td className="p-2 text-rose-700 font-medium">{c.duplicate_with || '-'}</td>
                          <td className="p-2 text-center font-bold text-amber-800">{c.rate_source || '-'}</td>
                          <td className="p-2 text-right font-mono font-bold text-slate-900">
                            LKR {Number(c.cost_impact).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                          </td>
                          <td className="p-2 text-slate-600 text-[11px]">{c.reason || '-'}</td>
                        </tr>
                      ))}

                      {/* Inline Add Row */}
                      <tr className="bg-slate-50 border-t-2 border-slate-300">
                        <td className="p-2">
                          <input
                            type="text"
                            placeholder="Ref (CR-04)"
                            value={newChangeItem.ref_code}
                            onChange={(e) => setNewChangeItem({ ...newChangeItem, ref_code: e.target.value })}
                            className="w-full text-xs p-1 rounded border border-slate-300 font-bold"
                          />
                        </td>
                        <td className="p-2">
                          <input
                            type="text"
                            placeholder="Package"
                            value={newChangeItem.package_sheet}
                            onChange={(e) => setNewChangeItem({ ...newChangeItem, package_sheet: e.target.value })}
                            className="w-full text-xs p-1 rounded border border-slate-300"
                          />
                        </td>
                        <td className="p-2">
                          <input
                            type="text"
                            placeholder="Item"
                            value={newChangeItem.item_code}
                            onChange={(e) => setNewChangeItem({ ...newChangeItem, item_code: e.target.value })}
                            className="w-full text-xs p-1 rounded border border-slate-300"
                          />
                        </td>
                        <td className="p-2">
                          <input
                            type="text"
                            placeholder="Description..."
                            value={newChangeItem.description}
                            onChange={(e) => setNewChangeItem({ ...newChangeItem, description: e.target.value })}
                            className="w-full text-xs p-1 rounded border border-slate-300"
                          />
                        </td>
                        <td className="p-2">
                          <input
                            type="text"
                            placeholder="Orig. Status"
                            value={newChangeItem.original_status}
                            onChange={(e) => setNewChangeItem({ ...newChangeItem, original_status: e.target.value })}
                            className="w-full text-xs p-1 rounded border border-slate-300"
                          />
                        </td>
                        <td className="p-2">
                          <input
                            type="text"
                            placeholder="REV 7 Action"
                            value={newChangeItem.rev7_action}
                            onChange={(e) => setNewChangeItem({ ...newChangeItem, rev7_action: e.target.value })}
                            className="w-full text-xs p-1 rounded border border-slate-300"
                          />
                        </td>
                        <td className="p-2">
                          <input
                            type="text"
                            placeholder="Duplicate with"
                            value={newChangeItem.duplicate_with}
                            onChange={(e) => setNewChangeItem({ ...newChangeItem, duplicate_with: e.target.value })}
                            className="w-full text-xs p-1 rounded border border-slate-300"
                          />
                        </td>
                        <td className="p-2">
                          <input
                            type="text"
                            placeholder="Rate Source"
                            value={newChangeItem.rate_source}
                            onChange={(e) => setNewChangeItem({ ...newChangeItem, rate_source: e.target.value })}
                            className="w-full text-xs p-1 rounded border border-slate-300"
                          />
                        </td>
                        <td className="p-2">
                          <input
                            type="number"
                            placeholder="Cost Impact"
                            value={newChangeItem.cost_impact}
                            onChange={(e) => setNewChangeItem({ ...newChangeItem, cost_impact: parseFloat(e.target.value) || 0 })}
                            className="w-full text-xs p-1 rounded border border-slate-300 text-right"
                          />
                        </td>
                        <td className="p-2 flex items-center gap-2">
                          <input
                            type="text"
                            placeholder="Reason"
                            value={newChangeItem.reason}
                            onChange={(e) => setNewChangeItem({ ...newChangeItem, reason: e.target.value })}
                            className="w-full text-xs p-1 rounded border border-slate-300"
                          />
                          <button
                            onClick={handleAddChangeRecord}
                            className="px-2.5 py-1 bg-purple-600 text-white rounded hover:bg-purple-700 font-bold"
                          >
                            Add
                          </button>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* RECONCILIATION VIEW */}
            {currentSection.section_type === 'RECONCILIATION' && (
              <div className="overflow-x-auto border border-slate-200 rounded-lg">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-[#5B9BD5] text-white font-bold text-[11px]">
                      <th className="p-2.5 min-w-[160px]">Scope Element</th>
                      <th className="p-2.5 min-w-[160px]">Source BOQ</th>
                      <th className="p-2.5 min-w-[170px]">Other Package</th>
                      <th className="p-2.5 min-w-[170px]">Consolidated Treatment</th>
                      <th className="p-2.5 w-28 text-right">Deduction (LKR)</th>
                      <th className="p-2.5 min-w-[180px]">Reason</th>
                      <th className="p-2.5 text-center w-20">Risk</th>
                      <th className="p-2.5 min-w-[180px]">Tender Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 bg-white">
                    {currentSection.reconciliation_records?.map((r: any) => (
                      <tr key={r.id} className="hover:bg-teal-50/20">
                        <td className="p-2.5 font-semibold text-slate-900">{r.scope_element}</td>
                        <td className="p-2.5 text-slate-700">{r.source_boq}</td>
                        <td className="p-2.5 text-slate-700">{r.other_package}</td>
                        <td className="p-2.5 text-teal-800 font-medium">{r.consolidated_treatment}</td>
                        <td className="p-2.5 text-right font-mono text-rose-600 font-semibold">{r.deduction_amount}</td>
                        <td className="p-2.5 text-slate-600 text-[11px]">{r.reason}</td>
                        <td className="p-2.5 text-center">
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800">
                            {r.risk}
                          </span>
                        </td>
                        <td className="p-2.5 text-slate-700 font-medium">{r.tender_action}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ------------------------------------------------------------- */}
      {/* Historical Rate Comparison Modal */}
      {/* ------------------------------------------------------------- */}
      {showRateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-xs">
          <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] flex flex-col overflow-hidden border border-slate-200">
            {/* Modal Header */}
            <div className="p-4 bg-slate-900 text-white flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <Calendar className="w-5 h-5 text-amber-400" />
                <div>
                  <h3 className="font-bold text-sm">Historical Rate Comparison & Year Selection</h3>
                  <p className="text-[11px] text-slate-300">
                    Project Base Year: <span className="font-bold text-amber-400">{selectedProject?.project_base_year}</span> • Select any year's rate to use
                  </p>
                </div>
              </div>
              <button onClick={() => setShowRateModal(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Search Input */}
            <div className="p-4 border-b border-slate-200 bg-slate-50 flex gap-2">
              <div className="relative flex-1">
                <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
                <input
                  type="text"
                  value={rateSearchQuery}
                  onChange={(e) => setRateSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && runHistoricalSearch()}
                  placeholder="Search item code or description (e.g. brickwork, concrete, cable, pipe)..."
                  className="w-full text-xs pl-9 pr-4 py-2.5 rounded-lg border border-slate-300 focus:outline-none focus:border-blue-500 bg-white"
                />
              </div>
              <button
                onClick={() => runHistoricalSearch()}
                disabled={histLoading}
                className="px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5"
              >
                {histLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                <span>Search</span>
              </button>
            </div>

            {/* Rate Comparison Body */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {histComparison && (
                <div>
                  <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg border border-blue-200 text-xs mb-3">
                    <div>
                      <span className="font-bold text-slate-900">{histComparison.canonical_description}</span>
                      <div className="text-slate-500 text-[11px]">
                        Average Rate across years: <b>LKR {histComparison.average_rate?.toLocaleString()}</b> • Range:{' '}
                        <b>LKR {histComparison.min_rate?.toLocaleString()} - {histComparison.max_rate?.toLocaleString()}</b>
                      </div>
                    </div>
                    <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-blue-100 text-blue-800">
                      {histComparison.all_rates?.length || 0} Rate Matches Found
                    </span>
                  </div>

                  {/* Year-by-Year Cards / Comparison Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {Object.entries(histComparison.rates_by_year || {}).map(([yearKey, rateList]: [string, any]) => (
                      <div key={yearKey} className="border border-slate-200 rounded-xl p-3 bg-white shadow-2xs space-y-2">
                        <div className="flex items-center justify-between border-b border-slate-100 pb-1.5">
                          <span className="font-extrabold text-sm text-slate-900">BSR {yearKey}</span>
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-100 text-amber-900">
                            {rateList.length} Items
                          </span>
                        </div>
                        <div className="space-y-1.5 max-h-48 overflow-y-auto">
                          {rateList.map((r: any) => {
                            const isChosen = selectedHistRate?.rate_item_id === r.rate_item_id;
                            return (
                              <div
                                key={r.rate_item_id}
                                onClick={() => setSelectedHistRate(r)}
                                className={`p-2 rounded-lg border text-xs cursor-pointer transition-all ${
                                  isChosen
                                    ? 'bg-blue-50 border-blue-500 ring-2 ring-blue-500/20'
                                    : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                                }`}
                              >
                                <div className="flex justify-between items-center">
                                  <span className="font-bold text-slate-900">{r.item_code}</span>
                                  <span className="font-mono font-bold text-blue-700">
                                    LKR {r.rate.toLocaleString()}
                                  </span>
                                </div>
                                <div className="text-[11px] text-slate-600 line-clamp-2 mt-0.5">{r.description}</div>
                                <div className="flex justify-between items-center text-[10px] text-slate-400 mt-1">
                                  <span>{r.province} ({r.unit})</span>
                                  {r.variance_pct !== undefined && (
                                    <span className={r.variance_pct >= 0 ? 'text-rose-600' : 'text-emerald-600'}>
                                      {r.variance_pct >= 0 ? `+${r.variance_pct}%` : `${r.variance_pct}%`}
                                    </span>
                                  )}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Rate Selection & Escalation Customization */}
              {selectedHistRate && (
                <div className="p-4 bg-emerald-50/70 border border-emerald-200 rounded-xl space-y-3">
                  <div className="flex items-center gap-2 text-xs font-bold text-emerald-900">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    <span>Selected Rate: BSR {selectedHistRate.year} • {selectedHistRate.item_code} (LKR {selectedHistRate.rate?.toLocaleString()} / {selectedHistRate.unit})</span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs">
                    <div>
                      <label className="block text-[11px] font-bold text-slate-600 mb-1">Quantity</label>
                      <input
                        type="number"
                        value={itemQty}
                        onChange={(e) => setItemQty(parseFloat(e.target.value) || 0)}
                        className="w-full p-2 bg-white rounded border border-slate-300 font-mono text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] font-bold text-slate-600 mb-1">Adjustment (LKR)</label>
                      <input
                        type="number"
                        value={itemAdjustment}
                        onChange={(e) => setItemAdjustment(parseFloat(e.target.value) || 0)}
                        placeholder="0.00"
                        className="w-full p-2 bg-white rounded border border-slate-300 font-mono text-sm"
                      />
                    </div>
                    <div className="sm:col-span-2">
                      <label className="block text-[11px] font-bold text-slate-600 mb-1">Rate Justification (Required for Audit)</label>
                      <input
                        type="text"
                        value={itemJustification}
                        onChange={(e) => setItemJustification(e.target.value)}
                        placeholder={`Adopted from ${selectedHistRate.year} BSR rate basis...`}
                        className="w-full p-2 bg-white rounded border border-slate-300 text-xs"
                      />
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-2 border-t border-emerald-200/60">
                    <div className="text-xs">
                      <span className="text-slate-500">Calculated Line Amount: </span>
                      <span className="font-mono font-bold text-emerald-900 text-sm">
                        LKR {(itemQty * (selectedHistRate.rate + itemAdjustment)).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                      </span>
                    </div>
                    <button
                      onClick={handleAddProjectItem}
                      className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold shadow-sm"
                    >
                      Add to Section BOQ
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* New Project Modal */}
      {/* ------------------------------------------------------------- */}
      {showNewProjectModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-xs">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-5 space-y-4 border border-slate-200">
            <div className="flex justify-between items-center border-b border-slate-100 pb-2">
              <h3 className="font-bold text-slate-900 text-sm">Create New Estimating Project</h3>
              <button onClick={() => setShowNewProjectModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Project Code</label>
                <input
                  type="text"
                  placeholder="e.g. MATARA-OT-REV7"
                  value={newProjData.project_code}
                  onChange={(e) => setNewProjData({ ...newProjData, project_code: e.target.value })}
                  className="w-full p-2 border border-slate-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Project Name</label>
                <input
                  type="text"
                  placeholder="e.g. Operating Theatre Renovation"
                  value={newProjData.project_name}
                  onChange={(e) => setNewProjData({ ...newProjData, project_name: e.target.value })}
                  className="w-full p-2 border border-slate-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Project Base Year (Distinct from Item Years)</label>
                <input
                  type="number"
                  value={newProjData.project_base_year}
                  onChange={(e) => setNewProjData({ ...newProjData, project_base_year: parseInt(e.target.value) || 2026 })}
                  className="w-full p-2 border border-slate-300 rounded-lg font-bold"
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Location</label>
                <input
                  type="text"
                  value={newProjData.location}
                  onChange={(e) => setNewProjData({ ...newProjData, location: e.target.value })}
                  className="w-full p-2 border border-slate-300 rounded-lg"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
              <button
                onClick={() => setShowNewProjectModal(false)}
                className="px-3 py-1.5 rounded-lg border border-slate-300 text-slate-600 font-semibold text-xs"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateProject}
                className="px-4 py-1.5 rounded-lg bg-blue-600 text-white font-bold text-xs hover:bg-blue-700"
              >
                Create Project
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* Add Section Modal */}
      {/* ------------------------------------------------------------- */}
      {showAddSectionModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-xs">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-5 space-y-4 border border-slate-200">
            <div className="flex justify-between items-center border-b border-slate-100 pb-2">
              <h3 className="font-bold text-slate-900 text-sm">Add Output Section / Scope Element</h3>
              <button onClick={() => setShowAddSectionModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Section Name</label>
                <input
                  type="text"
                  placeholder="e.g. Landscaping / Site Drainage"
                  value={newSecData.section_name}
                  onChange={(e) => setNewSecData({ ...newSecData, section_name: e.target.value })}
                  className="w-full p-2 border border-slate-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Section Type</label>
                <select
                  value={newSecData.section_type}
                  onChange={(e) => setNewSecData({ ...newSecData, section_type: e.target.value })}
                  className="w-full p-2 border border-slate-300 rounded-lg"
                >
                  <option value="BOQ">Standard BOQ Line Items</option>
                  <option value="DUPLICATION">Duplication Review (BOQ-Style)</option>
                  <option value="CHANGE_REGISTER">Consolidation Change Register</option>
                  <option value="RECONCILIATION">Scope Reconciliation</option>
                </select>
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Target Worksheet Name in Master Template</label>
                <input
                  type="text"
                  placeholder="e.g. Site Works - Reviewed, Added Renovation BOQ"
                  value={newSecData.target_sheet}
                  onChange={(e) => setNewSecData({ ...newSecData, target_sheet: e.target.value })}
                  className="w-full p-2 border border-slate-300 rounded-lg"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
              <button
                onClick={() => setShowAddSectionModal(false)}
                className="px-3 py-1.5 rounded-lg border border-slate-300 text-slate-600 font-semibold text-xs"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateSection}
                className="px-4 py-1.5 rounded-lg bg-blue-600 text-white font-bold text-xs hover:bg-blue-700"
              >
                Save Section
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* Template Mappings Modal */}
      {/* ------------------------------------------------------------- */}
      {showTemplateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-xs">
          <div className="bg-white rounded-2xl shadow-2xl max-w-3xl w-full max-h-[85vh] flex flex-col overflow-hidden border border-slate-200">
            <div className="p-4 bg-slate-900 text-white flex justify-between items-center">
              <div className="flex items-center gap-2">
                <SlidersHorizontal className="w-5 h-5 text-teal-400" />
                <h3 className="font-bold text-sm">Master Template Configuration & Sheet Mappings</h3>
              </div>
              <button onClick={() => setShowTemplateModal(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4 overflow-y-auto space-y-4 text-xs">
              <p className="text-slate-600">
                Registered Master Workbook: <b>Matara_OT_Renovation_Consolidated_BOQ_Estimate_Rev7_Electrical_Ancillary_Deduplicated.xlsx</b>
              </p>
              <div className="border border-slate-200 rounded-lg overflow-hidden">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-slate-100 text-slate-700 font-bold border-b border-slate-200">
                      <th className="p-2.5">Section Type</th>
                      <th className="p-2.5">Target Sheet</th>
                      <th className="p-2.5 text-center">Start Row</th>
                      <th className="p-2.5">Key Column Mappings</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {templates[0]?.mappings?.map((m: any) => (
                      <tr key={m.id} className="hover:bg-slate-50">
                        <td className="p-2.5 font-bold text-slate-800">{m.section_type}</td>
                        <td className="p-2.5 text-blue-700 font-semibold">{m.target_sheet}</td>
                        <td className="p-2.5 text-center font-mono">{m.start_row}</td>
                        <td className="p-2.5 text-slate-500 font-mono text-[11px]">
                          Desc:{m.description_column} • Qty:{m.quantity_column} • Rate:{m.rate_column} • Amt:{m.amount_column}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            <div className="p-3 bg-slate-50 border-t border-slate-200 flex justify-end">
              <button
                onClick={() => setShowTemplateModal(false)}
                className="px-4 py-1.5 bg-slate-800 text-white rounded-lg text-xs font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
