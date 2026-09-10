import React, { useState, useRef } from 'react';
import {
  UploadCloud,
  FileCheck,
  AlertTriangle,
  CheckCircle2,
  ExternalLink,
  ArrowRight,
  ShieldCheck,
  RefreshCw,
} from 'lucide-react';
import { api } from '../api/client';
import {
  PROVINCE_LIST,
  SRI_LANKA_PROVINCES,
  REVISION_OPTIONS,
  DATASET_TYPES,
  VAT_BASIS_OPTIONS,
} from '../constants/sriLanka';

interface ImportCenterPageProps {
  onNavigate: (tab: string, filterParams?: any) => void;
  onRefreshMetrics?: () => void;
}

export const ImportCenterPage: React.FC<ImportCenterPageProps> = ({
  onNavigate,
  onRefreshMetrics,
}) => {
  // Form State
  const [province, setProvince] = useState<string>('Southern');
  const [district, setDistrict] = useState<string>('Matara');
  const [year, setYear] = useState<number>(new Date().getFullYear());
  const [revision, setRevision] = useState<string>('First Half');
  const [datasetType, setDatasetType] = useState<string>('BSR Rate Book');
  const [vatBasis, setVatBasis] = useState<string>('Without VAT');
  const [categoryHint, setCategoryHint] = useState<string>('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Upload & Extraction Progress State
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // When province changes, update district default to first valid district
  const handleProvinceChange = (newProv: string) => {
    setProvince(newProv);
    const districts = SRI_LANKA_PROVINCES[newProv] || [];
    if (districts.length > 0) {
      setDistrict(districts[0]);
    }
  };

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelected = (file: File) => {
    const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    const allowed = ['.pdf', '.xlsx', '.xlsm', '.docx', '.csv', '.tsv', '.txt'];
    if (!allowed.includes(ext)) {
      setError(`Unsupported format "${ext}". Supported formats: PDF (.pdf), Excel (.xlsx, .xlsm), Word (.docx), CSV (.csv), TSV (.tsv), TXT (.txt)`);
      return;
    }
    if (file.size > 250 * 1024 * 1024) {
      setError('File exceeds maximum upload size of 250 MB.');
      return;
    }
    setError(null);
    setSelectedFile(file);
    setResult(null);
  };

  const handleUploadAndAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setError('Please select a file to upload.');
      return;
    }

    try {
      setIsUploading(true);
      setError(null);
      setUploadProgress(20);

      const formData = new FormData();
      formData.append('province', province);
      formData.append('district', district);
      formData.append('year', year.toString());
      formData.append('revision', revision);
      formData.append('dataset_type', datasetType);
      formData.append('vat_basis', vatBasis);
      if (categoryHint) {
        formData.append('category_hint', categoryHint);
      }
      formData.append('file', selectedFile);

      setUploadProgress(50);
      const res = await api.uploadDocument(formData);
      setUploadProgress(100);
      setResult(res);

      if (onRefreshMetrics) {
        onRefreshMetrics();
      }
    } catch (err: any) {
      setError(err.message || 'Upload and extraction failed.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleApproveValid = async () => {
    if (!result?.document_id) return;
    try {
      const res = await api.approveValidDocumentItems(result.document_id);
      alert(res.message);
      if (onRefreshMetrics) onRefreshMetrics();
      onNavigate('search', { province, district, year });
    } catch (err: any) {
      alert(err.message || 'Failed to approve valid items.');
    }
  };

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Import Center</h2>
        <p className="text-sm text-slate-500 mt-1">
          Upload official BSR documents (PDF, Excel .xlsx/.xlsm, Word .docx, CSV, TSV, TXT) up to 250 MB. The system automatically
          extracts rate items, stores the original file permanently, and routes questionable rows to the Review Queue.
        </p>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-600 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Upload and Metadata Card */}
      <form onSubmit={handleUploadAndAnalyze} className="bg-white border border-slate-200 rounded-2xl shadow-xs p-6 space-y-6">
        <h3 className="text-base font-bold text-slate-900 border-b border-slate-100 pb-3">
          Document Metadata Specification
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* Province */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Province <span className="text-rose-500">*</span>
            </label>
            <select
              value={province}
              onChange={(e) => handleProvinceChange(e.target.value)}
              className="w-full text-sm rounded-lg border border-slate-300 py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-600 bg-white"
            >
              {PROVINCE_LIST.map((p) => (
                <option key={p} value={p}>
                  {p === 'All Provinces' ? 'All Provinces (National / All Island)' : `${p} Province`}
                </option>
              ))}
            </select>
          </div>

          {/* District (Cascading) */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              District <span className="text-rose-500">*</span>
            </label>
            <select
              value={district}
              onChange={(e) => setDistrict(e.target.value)}
              className="w-full text-sm rounded-lg border border-slate-300 py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-600 bg-white"
            >
              {(SRI_LANKA_PROVINCES[province] || []).map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>

          {/* Year */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Year <span className="text-rose-500">*</span>
            </label>
            <input
              type="number"
              min="2015"
              max="2035"
              value={year}
              onChange={(e) => setYear(parseInt(e.target.value) || 2025)}
              className="w-full text-sm rounded-lg border border-slate-300 py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-600 bg-white"
            />
          </div>

          {/* Revision */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Revision <span className="text-rose-500">*</span>
            </label>
            <select
              value={revision}
              onChange={(e) => setRevision(e.target.value)}
              className="w-full text-sm rounded-lg border border-slate-300 py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-600 bg-white"
            >
              {REVISION_OPTIONS.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>

          {/* Dataset Type */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Dataset Type <span className="text-rose-500">*</span>
            </label>
            <select
              value={datasetType}
              onChange={(e) => setDatasetType(e.target.value)}
              className="w-full text-sm rounded-lg border border-slate-300 py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-600 bg-white"
            >
              {DATASET_TYPES.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>

          {/* VAT Basis */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              VAT Basis <span className="text-rose-500">*</span>
            </label>
            <select
              value={vatBasis}
              onChange={(e) => setVatBasis(e.target.value)}
              className="w-full text-sm rounded-lg border border-slate-300 py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-600 bg-white"
            >
              {VAT_BASIS_OPTIONS.map((v) => (
                <option key={v} value={v}>
                  {v}
                </option>
              ))}
            </select>
          </div>

          {/* Category Hint (Optional) */}
          <div className="md:col-span-3">
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Category Hint (Optional)
            </label>
            <input
              type="text"
              placeholder="e.g. Earth Work, Concrete Work, or leave blank to auto-detect"
              value={categoryHint}
              onChange={(e) => setCategoryHint(e.target.value)}
              className="w-full text-sm rounded-lg border border-slate-300 py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-600 bg-white"
            />
          </div>
        </div>

        {/* Drag and Drop Zone */}
        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleFileDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
            selectedFile
              ? 'border-blue-500 bg-blue-50/40'
              : 'border-slate-300 hover:border-slate-400 bg-slate-50/50 hover:bg-slate-50'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            accept=".pdf,.xlsx,.xlsm,.docx,.csv,.tsv,.txt"
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) {
                handleFileSelected(e.target.files[0]);
              }
            }}
          />

          <div className="flex flex-col items-center justify-center">
            {selectedFile ? (
              <FileCheck className="w-12 h-12 text-blue-600 mb-2" />
            ) : (
              <UploadCloud className="w-12 h-12 text-slate-400 mb-2" />
            )}

            {selectedFile ? (
              <div>
                <span className="font-semibold text-slate-900 text-sm">{selectedFile.name}</span>
                <span className="text-xs text-slate-500 block mt-0.5">
                  {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB • Click to replace file
                </span>
              </div>
            ) : (
              <div>
                <span className="font-medium text-slate-700 text-sm">
                  Click to select BSR document or drag and drop file here
                </span>
                <span className="text-xs text-slate-400 block mt-1">
                  Supported formats: PDF (.pdf), Excel (.xlsx, .xlsm), Word (.docx), CSV (.csv), TSV (.tsv), TXT (.txt) (Up to 250 MB)
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Upload Button & Progress */}
        <div className="flex items-center justify-between pt-2">
          <div className="text-xs text-slate-500">
            <span>Destination: </span>
            <span className="font-mono text-slate-700 font-medium">
              /data/uploads/{province}/{district}/{year}/{revision.replace(/\s+/g, '_')}/
            </span>
          </div>

          <button
            type="submit"
            disabled={!selectedFile || isUploading}
            className={`flex items-center gap-2 px-6 py-2.5 rounded-xl font-semibold text-sm transition-all ${
              !selectedFile || isUploading
                ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-500 text-white shadow-sm'
            }`}
          >
            {isUploading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Extracting Rates ({uploadProgress}%)...</span>
              </>
            ) : (
              <>
                <UploadCloud className="w-4 h-4" />
                <span>Upload & Analyze</span>
              </>
            )}
          </button>
        </div>
      </form>

      {/* Post-Upload Extraction Summary Card */}
      {result && (
        <div className="bg-white border border-slate-200 rounded-2xl shadow-xs p-6 space-y-6 animate-in fade-in duration-300">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-emerald-50 rounded-xl text-emerald-600">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-slate-900">{result.filename}</h3>
                <p className="text-xs text-slate-500">
                  {result.ocr_required ? (
                    <span className="text-purple-600 font-medium">Scanned PDF (OCR Required)</span>
                  ) : (
                    'Extraction completed successfully'
                  )}
                </p>
              </div>
            </div>

            <a
              href={`/api/documents/${result.document_id}/download`}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              <span>View Source File</span>
            </a>
          </div>

          {/* Stats Breakdown */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
              <span className="text-xs text-slate-500 font-semibold uppercase">Items Detected</span>
              <div className="text-2xl font-bold text-slate-900 mt-1">{result.items_detected}</div>
            </div>

            <div className="p-4 bg-emerald-50/50 rounded-xl border border-emerald-100">
              <span className="text-xs text-emerald-700 font-semibold uppercase">Valid Items</span>
              <div className="text-2xl font-bold text-emerald-800 mt-1">{result.valid_items}</div>
            </div>

            <div className="p-4 bg-amber-50/50 rounded-xl border border-amber-100">
              <span className="text-xs text-amber-700 font-semibold uppercase">Needs Review</span>
              <div className="text-2xl font-bold text-amber-800 mt-1">{result.needs_review}</div>
            </div>

            <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
              <span className="text-xs text-slate-500 font-semibold uppercase">Rejections / Errors</span>
              <div className="text-2xl font-bold text-slate-900 mt-1">{result.rejected_items || 0}</div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-between pt-2 border-t border-slate-100 flex-wrap gap-3">
            <div className="text-xs text-slate-500">
              Rates stored permanently under <span className="font-semibold text-slate-700">{province} • {district}</span>
            </div>

            <div className="flex items-center gap-3">
              {result.valid_items > 0 && (
                <button
                  onClick={handleApproveValid}
                  className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-xl shadow-xs"
                >
                  <ShieldCheck className="w-4 h-4" />
                  <span>Approve Valid Items ({result.valid_items})</span>
                </button>
              )}

              {result.needs_review > 0 && (
                <button
                  onClick={() => onNavigate('review', { source_file_id: result.document_id })}
                  className="flex items-center gap-2 px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold rounded-xl shadow-xs"
                >
                  <span>Review Data ({result.needs_review})</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              )}

              <button
                onClick={() => onNavigate('search', { province, district, year })}
                className="flex items-center gap-1.5 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold rounded-xl"
              >
                <span>Search Rates</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
