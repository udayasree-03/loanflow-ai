import React, { useState } from 'react';
import {
  FileText,
  Search,
  Plus,
  ArrowRight,
  Trash2,
  Clock,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
} from 'lucide-react';
import { LoanApplication, ApplicationStatus } from '../types';

interface ApplicationsListProps {
  applications: LoanApplication[];
  isLoading: boolean;
  onSelectApplication: (app: LoanApplication) => void;
  onNewApplication: () => void;
  onDeleteApplication: (id: string) => Promise<void>;
}

export const ApplicationsList: React.FC<ApplicationsListProps> = ({
  applications,
  isLoading,
  onSelectApplication,
  onNewApplication,
  onDeleteApplication,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const filtered = applications.filter((app) => {
    const matchesSearch =
      app.borrower_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      app.borrower_email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (app.property_address &&
        app.property_address.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesStatus =
      statusFilter === 'all' || app.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  const getStatusBadge = (status: ApplicationStatus) => {
    switch (status) {
      case 'approved':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-emerald-600" /> Approved
          </span>
        );
      case 'underwritten':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-purple-50 text-purple-700 border border-purple-200">
            <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-purple-600" /> Underwritten
          </span>
        );
      case 'processing':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
            <Clock className="w-3.5 h-3.5 mr-1 text-blue-600 animate-spin" /> Processing
          </span>
        );
      case 'rejected':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
            <XCircle className="w-3.5 h-3.5 mr-1 text-rose-600" /> Rejected
          </span>
        );
      case 'submitted':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            <AlertTriangle className="w-3.5 h-3.5 mr-1 text-amber-600" /> Submitted
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-600 border border-slate-200">
            <HelpCircle className="w-3.5 h-3.5 mr-1 text-slate-400" /> Draft
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner & Stats */}
      <div className="bg-gradient-to-r from-blue-900 via-indigo-900 to-slate-900 rounded-3xl p-6 sm:p-8 text-white shadow-xl relative overflow-hidden">
        <div className="absolute right-0 top-0 translate-x-12 -translate-y-12 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 max-w-2xl">
          <span className="text-xs font-bold tracking-widest uppercase bg-blue-500/20 text-blue-300 px-3 py-1 rounded-full border border-blue-400/30">
            Autonomous Mortgage Pipeline
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold mt-3 tracking-tight">
            AI Underwriting & Document Intelligence
          </h1>
          <p className="mt-2 text-sm sm:text-base text-slate-300">
            Instant multi-document ingestion (W-2s, 1040s, Paystubs), cross-verification fraud detection, and Fannie Mae conforming guideline evaluations powered by LangGraph.
          </p>
          <div className="mt-5 flex items-center space-x-3">
            <button
              onClick={onNewApplication}
              className="inline-flex items-center px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm rounded-xl shadow-lg shadow-blue-600/30 transition-all hover:scale-[1.02]"
            >
              <Plus className="w-4 h-4 mr-1.5" /> New Application
            </button>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search by borrower name, email, or address..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 text-sm bg-white border border-slate-200 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
          />
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Status:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 text-sm bg-white border border-slate-200 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-slate-700"
          >
            <option value="all">All Applications</option>
            <option value="draft">Draft</option>
            <option value="underwritten">Underwritten</option>
            <option value="processing">Processing</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
          </select>
        </div>
      </div>

      {/* Applications Table */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="p-12 text-center text-slate-500">
            <div className="inline-block animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full mb-3" />
            <p className="text-sm font-medium">Loading applications from database...</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-12 text-center">
            <div className="w-12 h-12 rounded-2xl bg-slate-100 text-slate-400 flex items-center justify-center mx-auto mb-3">
              <FileText className="w-6 h-6" />
            </div>
            <h3 className="font-semibold text-slate-800">No applications found</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              {searchTerm || statusFilter !== 'all'
                ? 'Try adjusting your search query or status filter.'
                : 'Get started by creating your first mortgage loan application.'}
            </p>
            {!searchTerm && statusFilter === 'all' && (
              <button
                onClick={onNewApplication}
                className="mt-4 px-4 py-2 bg-blue-600 text-white text-xs font-semibold rounded-xl hover:bg-blue-700 transition-colors"
              >
                Create Application
              </button>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50/75 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  <th className="py-3.5 px-6">Borrower</th>
                  <th className="py-3.5 px-4">Loan Amount</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4">Documents</th>
                  <th className="py-3.5 px-4">Created</th>
                  <th className="py-3.5 px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm">
                {filtered.map((app) => (
                  <tr
                    key={app.id}
                    className="hover:bg-blue-50/40 transition-colors group"
                  >
                    <td className="py-4 px-6">
                      <div className="font-semibold text-slate-900 group-hover:text-blue-600 transition-colors">
                        {app.borrower_name}
                      </div>
                      <div className="text-xs text-slate-500 mt-0.5">{app.borrower_email}</div>
                      {app.property_address && (
                        <div className="text-xs text-slate-400 mt-0.5 truncate max-w-xs">
                          {app.property_address}
                        </div>
                      )}
                    </td>
                    <td className="py-4 px-4">
                      <span className="font-semibold text-slate-900 text-base">
                        ${Number(app.loan_amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </span>
                    </td>
                    <td className="py-4 px-4">{getStatusBadge(app.status)}</td>
                    <td className="py-4 px-4">
                      <span className="inline-flex items-center text-xs font-medium bg-slate-100 text-slate-700 px-2.5 py-1 rounded-lg">
                        <FileText className="w-3.5 h-3.5 mr-1 text-slate-500" />
                        {app.documents?.length || 0} files
                      </span>
                    </td>
                    <td className="py-4 px-4 text-xs text-slate-500">
                      {new Date(app.created_at).toLocaleDateString(undefined, {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                      })}
                    </td>
                    <td className="py-4 px-6 text-right">
                      <div className="flex items-center justify-end space-x-2">
                        <button
                          onClick={() => onSelectApplication(app)}
                          className="inline-flex items-center px-3 py-1.5 text-xs font-semibold bg-blue-50 text-blue-700 hover:bg-blue-600 hover:text-white rounded-xl transition-all"
                        >
                          Workspace <ArrowRight className="w-3.5 h-3.5 ml-1" />
                        </button>
                        <button
                          onClick={async (e) => {
                            e.stopPropagation();
                            if (window.confirm(`Delete application for ${app.borrower_name}?`)) {
                              await onDeleteApplication(app.id);
                            }
                          }}
                          className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                          title="Delete application"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
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
