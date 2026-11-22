import React, { useRef, useState } from 'react';
import { UploadCloud, CheckCircle, AlertCircle, FileText, Loader2 } from 'lucide-react';

interface DocumentUploaderProps {
  applicationId: string;
  onUploadSuccess: () => void;
  onUploadFile: (file: File, docType?: string) => Promise<any>;
}

export const DocumentUploader: React.FC<DocumentUploaderProps> = ({
  onUploadFile,
  onUploadSuccess,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [docType, setDocType] = useState<string>('unclassified');
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const file = files[0];

    // Check size limit: 25MB
    if (file.size > 25 * 1024 * 1024) {
      setMessage({ type: 'error', text: 'File exceeds 25MB limit.' });
      return;
    }

    try {
      setIsUploading(true);
      setMessage(null);
      await onUploadFile(file, docType === 'unclassified' ? undefined : docType);
      setMessage({ type: 'success', text: `Uploaded "${file.name}" and extracted multi-page text successfully!` });
      onUploadSuccess();
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Upload failed.' });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="font-semibold text-slate-800 text-sm">Upload Mortgage Document</h4>
          <p className="text-xs text-slate-500">Supports PDF, PNG, JPG, TIFF up to 25MB</p>
        </div>

        <select
          value={docType}
          onChange={(e) => setDocType(e.target.value)}
          className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
        >
          <option value="unclassified">Auto-Classify Type</option>
          <option value="w2">Form W-2 (Wages)</option>
          <option value="paystub">Recent Paystub</option>
          <option value="form_1040">Form 1040 (Tax Return)</option>
          <option value="bank_statement">Bank Statement</option>
        </select>
      </div>

      {message && (
        <div
          className={`p-3 rounded-xl text-xs flex items-center space-x-2 ${
            message.type === 'success'
              ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
              : 'bg-rose-50 text-rose-800 border border-rose-200'
          }`}
        >
          {message.type === 'success' ? (
            <CheckCircle className="w-4 h-4 text-emerald-600 flex-shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
          )}
          <span>{message.text}</span>
        </div>
      )}

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          handleFiles(e.dataTransfer.files);
        }}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
          isDragging
            ? 'border-blue-500 bg-blue-50/60'
            : 'border-slate-200 hover:border-blue-400 hover:bg-slate-50/50'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.png,.jpg,.jpeg,.tiff"
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />

        {isUploading ? (
          <div className="py-2 flex flex-col items-center">
            <Loader2 className="w-7 h-7 text-blue-600 animate-spin mb-2" />
            <p className="text-xs font-semibold text-slate-700">Uploading & Extracting with PyMuPDF...</p>
            <p className="text-[11px] text-slate-400 mt-0.5">Performing text layout analysis and heuristic document classification</p>
          </div>
        ) : (
          <div className="flex flex-col items-center">
            <div className="w-10 h-10 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mb-2">
              <UploadCloud className="w-5 h-5" />
            </div>
            <p className="text-xs font-semibold text-slate-700">
              Click to select or drag & drop mortgage document
            </p>
            <p className="text-[11px] text-slate-400 mt-1">
              W-2s, 1040s, Paystubs, or Bank Statements (digital & scanned PDFs)
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
