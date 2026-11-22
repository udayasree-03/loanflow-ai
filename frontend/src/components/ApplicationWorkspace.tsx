import React, { useState } from 'react';
import {
  ArrowLeft,
  FileText,
  Trash2,
  Eye,
  Download,
  Calendar,
  Mail,
  Phone,
  MapPin,
  DollarSign,
  AlertCircle,
  FileCheck2,
} from 'lucide-react';
import { LoanApplication, DocumentDetail, UnderwritePayload, UnderwritingResult } from '../types';
import { DocumentUploader } from './DocumentUploader';
import { UnderwritingCard } from './UnderwritingCard';
import { DocumentViewerModal } from './DocumentViewerModal';
import {
  deleteDocument,
  fetchDocument,
  getDocumentDownloadUrl,
  triggerUnderwriting,
  uploadDocument,
} from '../services/api';

interface ApplicationWorkspaceProps {
  application: LoanApplication;
  onBack: () => void;
  onRefreshApplication: () => Promise<void>;
}

export const ApplicationWorkspace: React.FC<ApplicationWorkspaceProps> = ({
  application,
  onBack,
  onRefreshApplication,
}) => {
  const [selectedDoc, setSelectedDoc] = useState<DocumentDetail | null>(null);
  const [underwritingResult, setUnderwritingResult] = useState<UnderwritingResult | null>(null);
  const [isUnderwriting, setIsUnderwriting] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const handleUploadFile = async (file: File, docType?: string) => {
    return await uploadDocument(file, application.id, docType);
  };

  const handleViewDocument = async (docId: string) => {
    try {
      setActionError(null);
      const detail = await fetchDocument(docId);
      setSelectedDoc(detail);
    } catch (err: any) {
      setActionError(err.message || 'Failed to fetch document details.');
    }
  };

  const handleDeleteDoc = async (docId: string, fileName: string) => {
    if (!window.confirm(`Delete document "${fileName}"?`)) return;
    try {
      setActionError(null);
      await deleteDocument(docId);
      await onRefreshApplication();
    } catch (err: any) {
      setActionError(err.message || 'Failed to delete document.');
    }
  };

  const handleRunUnderwriting = async (payload: UnderwritePayload) => {
    try {
      setIsUnderwriting(true);
      setActionError(null);
      const result = await triggerUnderwriting(application.id, payload);
      setUnderwritingResult(result);
      await onRefreshApplication();
    } catch (err: any) {
      setActionError(err.message || 'Underwriting failed.');
    } finally {
      setIsUnderwriting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Navigation & Breadcrumb */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="inline-flex items-center text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors"
        >
          <ArrowLeft className="w-4 h-4 mr-1.5" /> Back to Applications Pipeline
        </button>

        <span className="text-xs text-slate-400">Application ID: {application.id}</span>
      </div>

      {actionError && (
        <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{actionError}</span>
        </div>
      )}

      {/* Application Overview Banner */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-3">
              <h2 className="text-2xl font-black text-slate-900 tracking-tight">
                {application.borrower_name}
              </h2>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-blue-100 text-blue-800">
                {application.status}
              </span>
            </div>

            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500 mt-2">
              <span className="flex items-center">
                <Mail className="w-3.5 h-3.5 mr-1 text-slate-400" /> {application.borrower_email}
              </span>
              {application.borrower_phone && (
                <span className="flex items-center">
                  <Phone className="w-3.5 h-3.5 mr-1 text-slate-400" /> {application.borrower_phone}
                </span>
              )}
              {application.property_address && (
                <span className="flex items-center">
                  <MapPin className="w-3.5 h-3.5 mr-1 text-slate-400" /> {application.property_address}
                </span>
              )}
              <span className="flex items-center">
                <Calendar className="w-3.5 h-3.5 mr-1 text-slate-400" />
                Submitted on {new Date(application.created_at).toLocaleDateString()}
              </span>
            </div>
          </div>

          <div className="bg-slate-50 rounded-xl p-4 border border-slate-100 sm:text-right">
            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
              Requested Loan Amount
            </span>
            <span className="text-2xl font-black text-slate-900">
              ${Number(application.loan_amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </span>
          </div>
        </div>
      </div>

      {/* Two-Column Workspace Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Documents & Ingestion (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          <DocumentUploader
            applicationId={application.id}
            onUploadFile={handleUploadFile}
            onUploadSuccess={onRefreshApplication}
          />

          {/* Uploaded Documents List */}
          <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-5 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center space-x-2">
                <FileCheck2 className="w-4 h-4 text-slate-600" />
                <h4 className="font-semibold text-slate-800 text-sm">
                  Attached Mortgage Documents ({application.documents?.length || 0})
                </h4>
              </div>
            </div>

            {application.documents?.length === 0 ? (
              <div className="p-6 text-center text-slate-400 text-xs">
                No documents uploaded yet. Upload a W-2, paystub, or tax return above.
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {application.documents?.map((doc) => (
                  <div
                    key={doc.id}
                    className="py-3 flex items-center justify-between group hover:bg-slate-50/60 rounded-xl px-2 -mx-2 transition-colors"
                  >
                    <div className="flex items-center space-x-3 overflow-hidden mr-2">
                      <div className="p-2 bg-blue-50 text-blue-600 rounded-lg flex-shrink-0">
                        <FileText className="w-4 h-4" />
                      </div>
                      <div className="overflow-hidden">
                        <p className="text-xs font-semibold text-slate-800 truncate" title={doc.file_name}>
                          {doc.file_name}
                        </p>
                        <div className="flex items-center space-x-1.5 text-[11px] text-slate-400 mt-0.5">
                          <span className="uppercase font-bold text-slate-600 px-1 py-0.2 bg-slate-100 rounded text-[10px]">
                            {doc.document_type}
                          </span>
                          <span>•</span>
                          <span>{(doc.file_size_bytes / 1024).toFixed(1)} KB</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-1">
                      <button
                        onClick={() => handleViewDocument(doc.id)}
                        className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                        title="View extracted text & analysis"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <a
                        href={getDocumentDownloadUrl(doc.id)}
                        download
                        className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
                        title="Download file"
                      >
                        <Download className="w-4 h-4" />
                      </a>
                      <button
                        onClick={() => handleDeleteDoc(doc.id, doc.file_name)}
                        className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                        title="Delete document"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Underwriting Decision Center (7 cols) */}
        <div className="lg:col-span-7">
          <UnderwritingCard
            underwriting={underwritingResult}
            isLoading={isUnderwriting}
            onRunUnderwriting={handleRunUnderwriting}
            defaultLoanAmount={Number(application.loan_amount)}
          />
        </div>
      </div>

      {/* Document Text Viewer Modal */}
      <DocumentViewerModal
        document={selectedDoc}
        onClose={() => setSelectedDoc(null)}
      />
    </div>
  );
};
