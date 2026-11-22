import React, { useState } from 'react';
import {
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Play,
  RotateCcw,
  ShieldAlert,
  Percent,
  Home,
  FileCheck,
  ChevronDown,
  ChevronUp,
  Terminal,
  Settings2,
} from 'lucide-react';
import { UnderwritingResult, UnderwritePayload } from '../types';

interface UnderwritingCardProps {
  underwriting: UnderwritingResult | null;
  isLoading: boolean;
  onRunUnderwriting: (payload: UnderwritePayload) => Promise<void>;
  defaultLoanAmount: number;
}

export const UnderwritingCard: React.FC<UnderwritingCardProps> = ({
  underwriting,
  isLoading,
  onRunUnderwriting,
  defaultLoanAmount,
}) => {
  const [showConfig, setShowConfig] = useState(false);
  const [showLogs, setShowLogs] = useState(false);
  const [propertyValue, setPropertyValue] = useState<string>(
    underwriting ? String(underwriting.dti_analysis.property_value) : String(Math.round(defaultLoanAmount * 1.25))
  );
  const [monthlyDebt, setMonthlyDebt] = useState<string>(
    underwriting ? String(underwriting.dti_analysis.monthly_non_housing_debt) : '400'
  );
  const [interestRate, setInterestRate] = useState<string>('6.5');
  const [loanTerm, setLoanTerm] = useState<string>('30');

  const handleExecute = async () => {
    const propVal = parseFloat(propertyValue) || undefined;
    const debt = parseFloat(monthlyDebt) || 0;
    const rate = parseFloat(interestRate) || 6.5;
    const term = parseInt(loanTerm, 10) || 30;

    await onRunUnderwriting({
      property_value: propVal,
      monthly_debt: debt,
      interest_rate_pct: rate,
      loan_term_years: term,
    });
  };

  const decision = underwriting?.decision;
  const dti = underwriting?.dti_analysis;
  const entities = underwriting?.financial_entities;
  const flags = underwriting?.flags || [];

  const getDecisionBadge = () => {
    if (!decision) return null;
    switch (decision.status) {
      case 'APPROVED':
        return (
          <div className="bg-emerald-50 border-2 border-emerald-500/50 rounded-2xl p-5 text-emerald-900 shadow-sm flex items-start space-x-3.5">
            <div className="p-2.5 bg-emerald-500 text-white rounded-xl shadow-md shadow-emerald-500/30">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <span className="font-extrabold text-lg tracking-tight text-emerald-950">
                  LOAN APPROVED
                </span>
                <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-emerald-200/80 text-emerald-900">
                  {(decision.confidence_score * 100).toFixed(0)}% Confidence
                </span>
              </div>
              <p className="text-xs text-emerald-800 mt-1 leading-relaxed">{decision.summary}</p>
            </div>
          </div>
        );
      case 'REFER_TO_HUMAN':
        return (
          <div className="bg-amber-50 border-2 border-amber-500/50 rounded-2xl p-5 text-amber-900 shadow-sm flex items-start space-x-3.5">
            <div className="p-2.5 bg-amber-500 text-white rounded-xl shadow-md shadow-amber-500/30">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <span className="font-extrabold text-lg tracking-tight text-amber-950">
                  REFER TO HUMAN UNDERWRITER
                </span>
                <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-amber-200/80 text-amber-900">
                  {(decision.confidence_score * 100).toFixed(0)}% Confidence
                </span>
              </div>
              <p className="text-xs text-amber-800 mt-1 leading-relaxed">{decision.summary}</p>
            </div>
          </div>
        );
      case 'REJECTED':
        return (
          <div className="bg-rose-50 border-2 border-rose-500/50 rounded-2xl p-5 text-rose-900 shadow-sm flex items-start space-x-3.5">
            <div className="p-2.5 bg-rose-500 text-white rounded-xl shadow-md shadow-rose-500/30">
              <XCircle className="w-6 h-6" />
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <span className="font-extrabold text-lg tracking-tight text-rose-950">
                  APPLICATION REJECTED
                </span>
                <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-rose-200/80 text-rose-900">
                  {(decision.confidence_score * 100).toFixed(0)}% Confidence
                </span>
              </div>
              <p className="text-xs text-rose-800 mt-1 leading-relaxed">{decision.summary}</p>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
        <div>
          <div className="flex items-center space-x-2">
            <Sparkles className="w-5 h-5 text-blue-600" />
            <h3 className="font-bold text-slate-900 text-lg tracking-tight">
              LangGraph Underwriting Engine
            </h3>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Conforming guideline evaluation, cross-verification & debt-to-income analysis
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowConfig(!showConfig)}
            className="p-2 rounded-xl text-slate-500 hover:text-slate-700 hover:bg-slate-100 text-xs font-medium flex items-center transition-colors"
            title="Adjust appraisal or loan assumptions"
          >
            <Settings2 className="w-4 h-4 mr-1" /> Assumptions
          </button>
          <button
            onClick={handleExecute}
            disabled={isLoading}
            className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-xl text-xs font-semibold shadow-md shadow-blue-500/20 transition-all disabled:opacity-50"
          >
            {isLoading ? (
              <>
                <RotateCcw className="w-3.5 h-3.5 mr-1.5 animate-spin" /> Evaluating...
              </>
            ) : underwriting ? (
              <>
                <RotateCcw className="w-3.5 h-3.5 mr-1.5" /> Re-Evaluate Agent
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 mr-1.5 fill-current" /> Run Underwriting
              </>
            )}
          </button>
        </div>
      </div>

      {/* Assumptions Panel (Collapsible) */}
      {showConfig && (
        <div className="p-4 bg-slate-50 rounded-xl border border-slate-200/80 space-y-3 text-xs">
          <h4 className="font-semibold text-slate-800 uppercase tracking-wider">
            Loan Underwriting Assumptions
          </h4>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div>
              <label className="text-slate-500 block mb-1">Property Value ($)</label>
              <input
                type="number"
                value={propertyValue}
                onChange={(e) => setPropertyValue(e.target.value)}
                className="w-full px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-xs"
              />
            </div>
            <div>
              <label className="text-slate-500 block mb-1">Monthly Other Debt ($)</label>
              <input
                type="number"
                value={monthlyDebt}
                onChange={(e) => setMonthlyDebt(e.target.value)}
                className="w-full px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-xs"
              />
            </div>
            <div>
              <label className="text-slate-500 block mb-1">Interest Rate (%)</label>
              <input
                type="number"
                step="0.125"
                value={interestRate}
                onChange={(e) => setInterestRate(e.target.value)}
                className="w-full px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-xs"
              />
            </div>
            <div>
              <label className="text-slate-500 block mb-1">Term (Years)</label>
              <select
                value={loanTerm}
                onChange={(e) => setLoanTerm(e.target.value)}
                className="w-full px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-xs"
              >
                <option value="15">15 Years</option>
                <option value="30">30 Years</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Decision Banner */}
      {decision ? (
        getDecisionBadge()
      ) : (
        <div className="p-8 text-center bg-slate-50/60 rounded-2xl border border-dashed border-slate-200">
          <Sparkles className="w-8 h-8 text-slate-400 mx-auto mb-2" />
          <h4 className="font-semibold text-slate-800 text-sm">Underwriting Not Yet Run</h4>
          <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
            Upload mortgage documents on the left and click "Run Underwriting" to trigger LangGraph agent guidelines assessment.
          </p>
        </div>
      )}

      {/* Key Financial Metrics & DTI Gauges */}
      {dti && entities && (
        <div className="space-y-4">
          <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
            Financial Health & Guidelines Radar
          </h4>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {/* Front-End DTI */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-600 flex items-center">
                  <Home className="w-3.5 h-3.5 mr-1 text-blue-500" /> Front-End DTI
                </span>
                <span className="text-[11px] font-medium text-slate-400">Max 28%</span>
              </div>
              <div className="flex items-baseline space-x-1.5">
                <span className="text-2xl font-black text-slate-900">{dti.front_end_dti_pct}%</span>
                <span className="text-xs text-slate-500">housing ratio</span>
              </div>
              <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${
                    dti.front_end_dti_pct <= 28 ? 'bg-emerald-500' : 'bg-amber-500'
                  }`}
                  style={{ width: `${Math.min(dti.front_end_dti_pct, 100)}%` }}
                />
              </div>
            </div>

            {/* Back-End DTI */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-600 flex items-center">
                  <Percent className="w-3.5 h-3.5 mr-1 text-indigo-500" /> Back-End DTI
                </span>
                <span className="text-[11px] font-semibold text-rose-500">Cap 43.0%</span>
              </div>
              <div className="flex items-baseline space-x-1.5">
                <span
                  className={`text-2xl font-black ${
                    dti.back_end_dti_pct <= 43 ? 'text-slate-900' : 'text-rose-600'
                  }`}
                >
                  {dti.back_end_dti_pct}%
                </span>
                <span className="text-xs text-slate-500">total debt</span>
              </div>
              <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${
                    dti.back_end_dti_pct <= 43 ? 'bg-emerald-500' : 'bg-rose-500'
                  }`}
                  style={{ width: `${Math.min(dti.back_end_dti_pct, 100)}%` }}
                />
              </div>
            </div>

            {/* LTV */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-600 flex items-center">
                  <Home className="w-3.5 h-3.5 mr-1 text-emerald-500" /> LTV Ratio
                </span>
                <span className="text-[11px] font-medium text-slate-400">Target &le; 80%</span>
              </div>
              <div className="flex items-baseline space-x-1.5">
                <span className="text-2xl font-black text-slate-900">{dti.ltv_ratio_pct}%</span>
                <span className="text-xs text-slate-500">loan-to-value</span>
              </div>
              <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${
                    dti.ltv_ratio_pct <= 80 ? 'bg-emerald-500' : 'bg-blue-500'
                  }`}
                  style={{ width: `${Math.min(dti.ltv_ratio_pct, 100)}%` }}
                />
              </div>
            </div>
          </div>

          {/* Monthly Payment Breakdown */}
          <div className="p-4 bg-slate-50/75 rounded-xl border border-slate-200/60 flex flex-wrap items-center justify-between gap-4 text-xs">
            <div>
              <span className="text-slate-500 block">Qualifying Monthly Income</span>
              <span className="font-bold text-slate-900 text-sm">
                ${dti.qualifying_monthly_income.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block">Monthly P&amp;I</span>
              <span className="font-semibold text-slate-800">
                ${dti.estimated_monthly_pi.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block">Est. Taxes &amp; Insurance</span>
              <span className="font-semibold text-slate-800">
                ${dti.estimated_monthly_escrow.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block">Total Monthly Housing</span>
              <span className="font-bold text-blue-700 text-sm">
                ${dti.total_monthly_housing_expense.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Discrepancy & Fraud Detection Radar */}
      {flags.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center space-x-2 text-rose-700">
            <ShieldAlert className="w-4 h-4" />
            <h4 className="text-xs font-bold uppercase tracking-wider">
              Anomalies & Discrepancy Flags ({flags.length})
            </h4>
          </div>

          <div className="space-y-2">
            {flags.map((flag, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-xl bg-rose-50/80 border border-rose-200 text-xs text-rose-900 flex items-start space-x-2.5"
              >
                <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold uppercase tracking-wider text-[11px] text-rose-800">
                      {flag.severity} Severity: {flag.category}
                    </span>
                    {flag.variance_pct !== undefined && flag.variance_pct !== null && (
                      <span className="px-2 py-0.5 rounded bg-rose-200/80 font-bold text-rose-900">
                        {flag.variance_pct}% variance
                      </span>
                    )}
                  </div>
                  <p className="mt-1 text-slate-800 font-medium">{flag.message}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Conditions Checklist */}
      {decision && decision.conditions.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center space-x-2 text-slate-700">
            <FileCheck className="w-4 h-4 text-blue-600" />
            <h4 className="text-xs font-bold uppercase tracking-wider">
              Underwriting Conditions & Requirements ({decision.conditions.length})
            </h4>
          </div>

          <div className="space-y-2 bg-slate-50 p-4 rounded-xl border border-slate-200/80">
            {decision.conditions.map((cond, idx) => (
              <label
                key={idx}
                className="flex items-start space-x-2.5 text-xs text-slate-700 cursor-pointer select-none hover:text-slate-900"
              >
                <input
                  type="checkbox"
                  className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 mt-0.5"
                />
                <span className="leading-snug">{cond}</span>
              </label>
            ))}
          </div>
        </div>
      )}

      {/* Reasoning Log (Collapsible) */}
      {underwriting && underwriting.reasoning_log.length > 0 && (
        <div className="pt-2 border-t border-slate-100">
          <button
            onClick={() => setShowLogs(!showLogs)}
            className="flex items-center justify-between w-full text-xs font-semibold text-slate-500 hover:text-slate-800 py-1"
          >
            <span className="flex items-center">
              <Terminal className="w-3.5 h-3.5 mr-1.5 text-slate-400" /> LangGraph Reasoning Logs
            </span>
            {showLogs ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          {showLogs && (
            <div className="mt-2 p-3 bg-slate-900 text-slate-300 font-mono text-[11px] rounded-xl space-y-1 max-h-48 overflow-y-auto">
              {underwriting.reasoning_log.map((log, idx) => (
                <div key={idx} className="leading-relaxed">
                  &gt; {log}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
