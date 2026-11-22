import React from 'react';
import { X, FileText, Download, CheckCircle2, AlertCircle } from 'lucide-react';
import { DocumentDetail } from '../types';
import { getDocumentDownloadUrl } from '../services/api';

interface DocumentViewerModalProps {
  document: DocumentDetail | null;
  onClose: () => void;
}

export const DocumentViewerModal: React.FC<DocumentViewerModalProps> = ({
  document,
  onClose,
}) => {
  if (!document) return null;

  const extraction = document.extraction_result;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="relative bg-white rounded-2xl max-w-3xl w-full shadow-2xl border border-slate-100 overflow-hidden max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 text-blue-700 rounded-xl">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900 text-base">{document.file_name}</h3>
              <div className="flex items-center space-x-2 text-xs text-slate-500 mt-0.5">
                <span className="uppercase font-semibold tracking-wider px-1.5 py-0.5 bg-slate-100 rounded text-slate-700">
                  {document.document_type}
                </span>
                <span>•</span>
                <span>{(document.file_size_bytes / 1024).toFixed(1)} KB</span>
                <span>•</span>
                <span>{extraction ? `${extraction.page_count} Page(s)` : 'No pages'}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <a
              href={getDocumentDownloadUrl(document.id)}
              download
              className="inline-flex items-center px-3 py-1.5 text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg transition-colors"
            >
              <Download className="w-3.5 h-3.5 mr-1" /> Download
            </a>
            <button
              onClick={onClose}
              className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-4 flex-1">
          {extraction ? (
            <>
              <div className="flex items-center justify-between bg-emerald-50 border border-emerald-200/80 rounded-xl p-3 text-xs text-emerald-800">
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span className="font-medium">
                    Extracted via {extraction.extraction_method.toUpperCase()} Layout Engine
                  </span>
                </div>
                {extraction.confidence_score !== null && (
                  <span className="bg-emerald-100 px-2 py-0.5 rounded font-semibold">
                    Confidence: {(extraction.confidence_score * 100).toFixed(0)}%
                  </span>
                )}
              </div>

              <div>
                <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                  Extracted Raw Text
                </h4>
                <div className="bg-slate-900 text-slate-200 font-mono text-xs rounded-xl p-4 overflow-x-auto max-h-96 whitespace-pre-wrap leading-relaxed selection:bg-blue-600">
                  {extraction.raw_text || '(No text extracted from document)'}
                </div>
              </div>
            </>
          ) : (
            <div className="p-8 text-center text-slate-500">
              <AlertCircle className="w-8 h-8 text-amber-500 mx-auto mb-2" />
              <p className="text-sm font-medium">No extraction results available for this document.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
