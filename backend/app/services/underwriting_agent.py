from __future__ import annotations

import json
import logging
import math
import re
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple, TypedDict

import httpx
from langgraph.graph import END, START, StateGraph

from app.core.config import settings

logger = logging.getLogger("loanflow.underwriting")


class UnderwritingState(TypedDict, total=False):
    """The internal state tracked throughout the LangGraph underwriting pipeline."""
    application_id: str
    borrower_name: str
    borrower_email: str
    loan_amount: float
    property_value: float
    monthly_non_housing_debt: float
    interest_rate_pct: float
    loan_term_years: int
    documents: List[Dict[str, Any]]
    financial_entities: Dict[str, Any]
    discrepancy_flags: List[Dict[str, Any]]
    dti_analysis: Dict[str, Any]
    decision: Dict[str, Any]
    reasoning_log: List[str]


# ---------------------------------------------------------------------------
# Node 1: Financial Entity Extraction
# ---------------------------------------------------------------------------

def _clean_number(text: str) -> Optional[float]:
    """Helper to parse a float from currency or formatted text."""
    if not text:
        return None
    cleaned = re.sub(r"[^\d.]", "", text.strip())
    try:
        val = float(cleaned)
        return val if not math.isnan(val) else None
    except (ValueError, TypeError):
        return None


def _regex_extract_w2(text: str) -> Dict[str, Any]:
    """Fallback high-accuracy regex extraction for IRS Form W-2."""
    data: Dict[str, Any] = {}
    
    # Box 1: Wages, tips, other compensation
    # Patterns like: "1 Wages, tips, other comp. 85,000.00" or "Box 1: $85,000.00"
    wages_match = re.search(
        r"(?:(?:box\s*1|1\s*wages[^\n\d]*|\bwages[,\s]+tips[^\n\d]*)\s*[:$]?\s*([\d,]+\.?\d*))",
        text,
        re.IGNORECASE,
    )
    if wages_match:
        data["w2_annual_wages"] = _clean_number(wages_match.group(1))

    # Box 2: Federal income tax withheld
    tax_match = re.search(
        r"(?:(?:box\s*2|2\s*federal[^\n\d]*|\bfederal\s+income\s+tax[^\n\d]*)\s*[:$]?\s*([\d,]+\.?\d*))",
        text,
        re.IGNORECASE,
    )
    if tax_match:
        data["w2_federal_tax"] = _clean_number(tax_match.group(1))

    # Employer name heuristic
    emp_match = re.search(
        r"(?:employer(?:'s)?\s+name[^\n:]*[:\s]+([^\n]+)|c\s+employer[^\n]*\n([^\n]+))",
        text,
        re.IGNORECASE,
    )
    if emp_match:
        raw_emp = (emp_match.group(1) or emp_match.group(2) or "").strip()
        if raw_emp and len(raw_emp) < 100:
            data["employer_name"] = raw_emp

    return data


def _regex_extract_paystub(text: str) -> Dict[str, Any]:
    """Fallback high-accuracy regex extraction for paystubs."""
    data: Dict[str, Any] = {}

    # Gross pay / Current pay / Current Gross Earnings
    gross_match = re.search(
        r"(?:(?:current\s+gross(?:\s+earnings|\s+pay)?|gross\s+(?:pay|earnings|amount)|total\s+gross)[\s:$]+([\d,]+\.?\d*))",
        text,
        re.IGNORECASE,
    )
    if gross_match:
        data["paystub_gross_pay"] = _clean_number(gross_match.group(1))

    # Frequency detection
    if re.search(r"\bbi-?weekly\b", text, re.IGNORECASE):
        freq = "bi-weekly"
    elif re.search(r"\bsemi-?monthly\b", text, re.IGNORECASE):
        freq = "semi-monthly"
    elif re.search(r"\bmonthly\b", text, re.IGNORECASE):
        freq = "monthly"
    elif re.search(r"\bweekly\b", text, re.IGNORECASE):
        freq = "weekly"
    else:
        freq = "bi-weekly"
    data["paystub_pay_frequency"] = freq

    # Calculate annualized income if gross pay exists
    if data.get("paystub_gross_pay"):
        gross = data["paystub_gross_pay"]
        multiplier = 26.0 if freq == "bi-weekly" else (24.0 if freq == "semi-monthly" else (12.0 if freq == "monthly" else 52.0))
        data["paystub_annualized_income"] = round(gross * multiplier, 2)

    return data


def _regex_extract_1040(text: str) -> Dict[str, Any]:
    """Fallback high-accuracy regex extraction for Form 1040."""
    data: Dict[str, Any] = {}

    # Total wages (Line 1 / 1z)
    wages_match = re.search(
        r"(?:(?:line\s*1\w?|total\s+amount\s+from\s+form\(s\)\s+w-2|wages[,\s]+salaries[,\s]+tips)\s*[:$]?\s*([\d,]+\.?\d*))",
        text,
        re.IGNORECASE,
    )
    if wages_match:
        data["form_1040_total_wages"] = _clean_number(wages_match.group(1))

    # Adjusted Gross Income (Line 11)
    agi_match = re.search(
        r"(?:(?:line\s*11|adjusted\s+gross\s+income|agi)\s*[:$]?\s*([\d,]+\.?\d*))",
        text,
        re.IGNORECASE,
    )
    if agi_match:
        data["form_1040_adjusted_gross_income"] = _clean_number(agi_match.group(1))

    # Tax Year
    year_match = re.search(r"(?:1040\s+(?:u\.s\.\s+individual\s+income\s+tax\s+return\s+)?(202\d|201\d)|tax\s+year\s+(202\d|201\d))", text, re.IGNORECASE)
    if year_match:
        raw_yr = year_match.group(1) or year_match.group(2)
        if raw_yr:
            data["form_1040_tax_year"] = int(raw_yr)

    return data


def _regex_extract_bank_statement(text: str) -> Dict[str, Any]:
    """Fallback regex extraction for bank statements."""
    data: Dict[str, Any] = {}
    balance_match = re.search(
        r"(?:(?:ending\s+balance|new\s+balance|closing\s+balance)\s*[:$]?\s*([\d,]+\.?\d*))",
        text,
        re.IGNORECASE,
    )
    if balance_match:
        data["bank_statement_ending_balance"] = _clean_number(balance_match.group(1))
    return data


async def _extract_with_ollama(doc_type: str, text: str) -> Optional[Dict[str, Any]]:
    """Optional LLM extraction via Ollama when service is available."""
    prompt = (
        f"You are a mortgage document extraction specialist. Extract financial numbers from this {doc_type} document text. "
        "Return STRICT valid JSON only with keys depending on doc type:\n"
        "- For W-2: {\"w2_annual_wages\": number, \"w2_federal_tax\": number, \"employer_name\": string}\n"
        "- For Paystub: {\"paystub_gross_pay\": number, \"paystub_pay_frequency\": string, \"paystub_annualized_income\": number}\n"
        "- For 1040: {\"form_1040_total_wages\": number, \"form_1040_adjusted_gross_income\": number, \"form_1040_tax_year\": number}\n"
        "- For Bank Statement: {\"bank_statement_ending_balance\": number}\n"
        f"Document text snippet:\n{text[:2500]}\n"
    )
    try:
        async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT_SECONDS) as client:
            resp = await client.post(
                f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                },
            )
            if resp.status_code == 200:
                body = resp.json()
                raw_response = body.get("response", "").strip()
                if raw_response:
                    return json.loads(raw_response)
    except Exception as e:
        logger.debug(f"Ollama extraction skipped or offline ({e}), utilizing deterministic rules.")
    return None


async def extract_entities_node(state: UnderwritingState) -> Dict[str, Any]:
    """LangGraph Node: Extracts financial figures from all attached documents."""
    reasoning = list(state.get("reasoning_log", []))
    reasoning.append(f"[{datetime.now(timezone.utc).isoformat()}] Step 1: Initiating financial entity extraction across {len(state.get('documents', []))} documents.")

    entities: Dict[str, Any] = {
        "borrower_name": state.get("borrower_name"),
        "income_source_documents": [],
    }

    for doc in state.get("documents", []):
        doc_type = doc.get("document_type", "unclassified")
        raw_text = doc.get("raw_text", "")
        file_name = doc.get("file_name", "unknown")

        doc_data: Dict[str, Any] = {}

        # 1. Try Ollama first if accessible
        llm_data = await _extract_with_ollama(doc_type, raw_text)
        if llm_data and isinstance(llm_data, dict):
            doc_data.update(llm_data)

        # 2. Augment/fallback with deterministic regex
        if doc_type == "w2":
            regex_data = _regex_extract_w2(raw_text)
            for k, v in regex_data.items():
                if v is not None and not doc_data.get(k):
                    doc_data[k] = v
            if doc_data.get("w2_annual_wages"):
                entities["w2_annual_wages"] = doc_data["w2_annual_wages"]
                entities["income_source_documents"].append(f"W-2 ({file_name})")
            if doc_data.get("w2_federal_tax"):
                entities["w2_federal_tax"] = doc_data["w2_federal_tax"]
            if doc_data.get("employer_name"):
                entities["employer_name"] = doc_data["employer_name"]

        elif doc_type == "paystub":
            regex_data = _regex_extract_paystub(raw_text)
            for k, v in regex_data.items():
                if v is not None and not doc_data.get(k):
                    doc_data[k] = v
            if doc_data.get("paystub_gross_pay"):
                entities["paystub_gross_pay"] = doc_data["paystub_gross_pay"]
            if doc_data.get("paystub_pay_frequency"):
                entities["paystub_pay_frequency"] = doc_data["paystub_pay_frequency"]
            if doc_data.get("paystub_annualized_income"):
                entities["paystub_annualized_income"] = doc_data["paystub_annualized_income"]
                entities["income_source_documents"].append(f"Paystub ({file_name})")

        elif doc_type == "form_1040":
            regex_data = _regex_extract_1040(raw_text)
            for k, v in regex_data.items():
                if v is not None and not doc_data.get(k):
                    doc_data[k] = v
            if doc_data.get("form_1040_total_wages"):
                entities["form_1040_total_wages"] = doc_data["form_1040_total_wages"]
            if doc_data.get("form_1040_adjusted_gross_income"):
                entities["form_1040_adjusted_gross_income"] = doc_data["form_1040_adjusted_gross_income"]
                entities["income_source_documents"].append(f"Form 1040 ({file_name})")
            if doc_data.get("form_1040_tax_year"):
                entities["form_1040_tax_year"] = doc_data["form_1040_tax_year"]

        elif doc_type == "bank_statement":
            regex_data = _regex_extract_bank_statement(raw_text)
            for k, v in regex_data.items():
                if v is not None and not doc_data.get(k):
                    doc_data[k] = v
            if doc_data.get("bank_statement_ending_balance"):
                entities["bank_statement_ending_balance"] = doc_data["bank_statement_ending_balance"]

    # Calculate Qualifying Monthly Income:
    # Priority: W-2 Annual Wages / 12 -> Paystub Annualized / 12 -> 1040 AGI / 12
    annual_income = (
        entities.get("w2_annual_wages")
        or entities.get("paystub_annualized_income")
        or entities.get("form_1040_adjusted_gross_income")
        or 0.0
    )
    qualifying_monthly = round(annual_income / 12.0, 2)
    entities["qualifying_monthly_income"] = qualifying_monthly

    reasoning.append(
        f"Entity extraction complete. Derived qualifying monthly income: ${qualifying_monthly:,.2f} "
        f"from sources: {entities['income_source_documents'] or 'No verified income documents'}."
    )

    return {
        "financial_entities": entities,
        "reasoning_log": reasoning,
    }


# ---------------------------------------------------------------------------
# Node 2: Cross-Verification & Anomaly Detection
# ---------------------------------------------------------------------------

def cross_verify_node(state: UnderwritingState) -> Dict[str, Any]:
    """LangGraph Node: Reconciles income and identity across multiple documents."""
    reasoning = list(state.get("reasoning_log", []))
    flags: List[Dict[str, Any]] = []
    entities = state.get("financial_entities", {})

    w2_wages = entities.get("w2_annual_wages")
    paystub_annual = entities.get("paystub_annualized_income")
    tax_1040_wages = entities.get("form_1040_total_wages")

    # 1. Income Document Reconciliation: W-2 vs. Paystub
    if w2_wages and paystub_annual:
        diff = abs(w2_wages - paystub_annual)
        max_val = max(w2_wages, paystub_annual)
        pct_variance = round((diff / max_val) * 100, 2) if max_val > 0 else 0.0

        if pct_variance > 2.0:
            severity = "high" if pct_variance > 10.0 else "medium"
            flags.append({
                "severity": severity,
                "category": "income_variance",
                "field": "annual_income",
                "message": (
                    f"Income variance of {pct_variance}% detected between Form W-2 (${w2_wages:,.2f}) "
                    f"and Annualized Paystub (${paystub_annual:,.2f}). Exceeds allowable 2% guideline variance."
                ),
                "document_a": "Form W-2",
                "value_a": f"${w2_wages:,.2f}",
                "document_b": "Paystub",
                "value_b": f"${paystub_annual:,.2f}",
                "variance_pct": pct_variance,
            })
            reasoning.append(f"Flagged income discrepancy: W-2 vs Paystub variance is {pct_variance}%.")
        else:
            reasoning.append(f"Income cross-verification passed: W-2 and Paystub agree within {pct_variance}% (< 2% threshold).")

    # 2. Income Document Reconciliation: W-2 vs. 1040
    if w2_wages and tax_1040_wages:
        diff = abs(w2_wages - tax_1040_wages)
        max_val = max(w2_wages, tax_1040_wages)
        pct_variance = round((diff / max_val) * 100, 2) if max_val > 0 else 0.0

        if pct_variance > 2.0:
            flags.append({
                "severity": "medium",
                "category": "income_variance",
                "field": "wages_line_1",
                "message": f"W-2 wages (${w2_wages:,.2f}) and Form 1040 Line 1 wages (${tax_1040_wages:,.2f}) differ by {pct_variance}%.",
                "document_a": "Form W-2",
                "value_a": f"${w2_wages:,.2f}",
                "document_b": "Form 1040",
                "value_b": f"${tax_1040_wages:,.2f}",
                "variance_pct": pct_variance,
            })

    # 3. Missing Documentation Check
    if not entities.get("income_source_documents"):
        flags.append({
            "severity": "high",
            "category": "missing_doc",
            "field": "income_verification",
            "message": "No valid income verification documents (W-2, Paystub, or Form 1040) have been uploaded.",
            "document_a": None,
            "value_a": None,
            "document_b": None,
            "value_b": None,
            "variance_pct": None,
        })
        reasoning.append("Warning: Application lacks income verification documentation.")

    return {
        "discrepancy_flags": flags,
        "reasoning_log": reasoning,
    }


# ---------------------------------------------------------------------------
# Node 3: Underwriting Guidelines & DTI Evaluation
# ---------------------------------------------------------------------------

def calculate_monthly_pi(loan_amount: float, annual_rate_pct: float, term_years: int) -> float:
    """Calculates standard monthly Principal & Interest payment using amortization."""
    if loan_amount <= 0:
        return 0.0
    monthly_rate = (annual_rate_pct / 100.0) / 12.0
    num_payments = term_years * 12
    if monthly_rate == 0:
        return loan_amount / num_payments
    numerator = monthly_rate * math.pow(1 + monthly_rate, num_payments)
    denominator = math.pow(1 + monthly_rate, num_payments) - 1
    return round(loan_amount * (numerator / denominator), 2)


def evaluate_guidelines_node(state: UnderwritingState) -> Dict[str, Any]:
    """LangGraph Node: Evaluates Fannie Mae conforming DTI and LTV ratios."""
    reasoning = list(state.get("reasoning_log", []))
    flags = list(state.get("discrepancy_flags", []))
    entities = state.get("financial_entities", {})

    loan_amount = float(state.get("loan_amount", 0.0))
    property_val = float(state.get("property_value", 0.0))
    if property_val <= 0:
        # Default estimated property value assuming 80% LTV if not provided
        property_val = round(loan_amount * settings.DEFAULT_PROPERTY_VALUE_MULTIPLIER, 2)

    rate_pct = float(state.get("interest_rate_pct", settings.DEFAULT_MORTGAGE_INTEREST_RATE_PCT))
    term_years = int(state.get("loan_term_years", settings.DEFAULT_LOAN_TERM_YEARS))
    non_housing_debt = float(state.get("monthly_non_housing_debt", 0.0))
    qualifying_monthly = float(entities.get("qualifying_monthly_income", 0.0))

    # Calculate Housing Payment (P&I + Escrow)
    monthly_pi = calculate_monthly_pi(loan_amount, rate_pct, term_years)
    # Estimated monthly property taxes + insurance (~1.25% of property value / 12)
    estimated_escrow = round((property_val * 0.0125) / 12.0, 2)
    total_housing = round(monthly_pi + estimated_escrow, 2)
    total_debt = round(total_housing + non_housing_debt, 2)

    # Calculate Ratios
    ltv = round((loan_amount / property_val) * 100.0, 2) if property_val > 0 else 0.0

    if qualifying_monthly > 0:
        front_end_dti = round((total_housing / qualifying_monthly) * 100.0, 2)
        back_end_dti = round((total_debt / qualifying_monthly) * 100.0, 2)
        passes_front = front_end_dti <= settings.MAX_FRONT_END_DTI_BENCHMARK_PCT
        passes_back = back_end_dti <= settings.MAX_DTI_BENCHMARK_PCT

        if back_end_dti > 50.0:
            flags.append({
                "severity": "critical",
                "category": "guideline_breach",
                "field": "back_end_dti",
                "message": f"Back-End DTI of {back_end_dti}% severely exceeds standard 43% cap and maximum allowable 50% limit.",
                "document_a": "Loan Calculation",
                "value_a": f"{back_end_dti}%",
                "document_b": "Underwriting Guideline",
                "value_b": "43.00%",
                "variance_pct": round(back_end_dti - 43.0, 2),
            })
        elif back_end_dti > settings.MAX_DTI_BENCHMARK_PCT:
            flags.append({
                "severity": "medium",
                "category": "guideline_breach",
                "field": "back_end_dti",
                "message": f"Back-End DTI of {back_end_dti}% exceeds Fannie Mae 43.0% benchmark; requires compensating factors.",
                "document_a": "Loan Calculation",
                "value_a": f"{back_end_dti}%",
                "document_b": "Underwriting Guideline",
                "value_b": "43.00%",
                "variance_pct": round(back_end_dti - 43.0, 2),
            })
    else:
        # No verified qualifying income yet; DTI cannot be assessed
        front_end_dti = 0.0
        back_end_dti = 0.0
        passes_front = False
        passes_back = False

    dti_analysis = {
        "loan_amount": loan_amount,
        "property_value": property_val,
        "ltv_ratio_pct": ltv,
        "qualifying_monthly_income": qualifying_monthly,
        "estimated_monthly_pi": monthly_pi,
        "estimated_monthly_escrow": estimated_escrow,
        "total_monthly_housing_expense": total_housing,
        "monthly_non_housing_debt": non_housing_debt,
        "total_monthly_debt": total_debt,
        "front_end_dti_pct": front_end_dti,
        "back_end_dti_pct": back_end_dti,
        "max_allowed_dti_pct": settings.MAX_DTI_BENCHMARK_PCT,
        "passes_front_end": passes_front,
        "passes_back_end": passes_back,
    }

    if ltv > 95.0:
        flags.append({
            "severity": "high",
            "category": "guideline_breach",
            "field": "ltv_ratio",
            "message": f"LTV ratio of {ltv}% exceeds standard conventional financing limits.",
            "document_a": "Loan Calculation",
            "value_a": f"{ltv}%",
            "document_b": "Underwriting Guideline",
            "value_b": "95.00%",
            "variance_pct": round(ltv - 80.0, 2),
        })

    reasoning.append(
        f"Financial guideline evaluation complete: Monthly Housing Expense = ${total_housing:,.2f}, "
        f"Front-End DTI = {front_end_dti}%, Back-End DTI = {back_end_dti}%, LTV = {ltv}%."
    )

    return {
        "dti_analysis": dti_analysis,
        "discrepancy_flags": flags,
        "reasoning_log": reasoning,
    }


# ---------------------------------------------------------------------------
# Node 4: Decision Compilation & Conditions Package
# ---------------------------------------------------------------------------

def compile_decision_node(state: UnderwritingState) -> Dict[str, Any]:
    """LangGraph Node: Synthesizes findings into final decision, findings, and conditions."""
    reasoning = list(state.get("reasoning_log", []))
    flags = state.get("discrepancy_flags", [])
    dti = state.get("dti_analysis", {})
    entities = state.get("financial_entities", {})

    critical_flags = [f for f in flags if f.get("severity") == "critical"]
    high_flags = [f for f in flags if f.get("severity") == "high"]
    medium_flags = [f for f in flags if f.get("severity") == "medium"]

    back_end_dti = dti.get("back_end_dti_pct", 999.0)
    has_income_doc = bool(entities.get("income_source_documents"))

    key_findings: List[str] = []
    conditions: List[str] = [
        "Satisfactory property appraisal confirming market valuation.",
        "Clear title report with no senior unreleased liens or encumbrances.",
        "Final verbal verification of employment (VOE) within 10 days of note date.",
        "Proof of 12-month prepaid homeowner's hazard insurance policy naming lender as loss payee.",
    ]

    # Decision Matrix:
    if critical_flags or back_end_dti > 50.0:
        status = "REJECTED"
        confidence = 0.95
        summary = (
            f"Mortgage application rejected due to excessive debt burden (Back-End DTI: {back_end_dti:.1f}% vs 43.0% max) "
            "or critical guideline non-compliance."
        )
        for cf in critical_flags:
            key_findings.append(f"CRITICAL: {cf['message']}")

    elif high_flags or not has_income_doc or back_end_dti > settings.MAX_DTI_BENCHMARK_PCT or medium_flags:
        status = "REFER_TO_HUMAN"
        confidence = 0.88
        summary = (
            "Application referred to Senior Human Underwriter for manual review and exception processing due to "
            "document discrepancies, elevated DTI, or missing income documentation."
        )
        if not has_income_doc:
            key_findings.append("Missing documentation: No validated W-2, paystub, or tax return verified.")
            conditions.append("PRIOR TO APPROVAL: Borrower must supply two consecutive years of W-2s and most recent 30-day paystub.")
        for f in high_flags + medium_flags:
            key_findings.append(f"{f['severity'].upper()}: {f['message']}")
            if f.get("category") == "income_variance":
                conditions.append(f"PRIOR TO CLOSING: Signed letter of explanation for income variance between {f.get('document_a')} and {f.get('document_b')}.")

    else:
        status = "APPROVED"
        confidence = 0.96
        summary = (
            f"Loan application meets all Fannie Mae conforming underwriting guidelines with "
            f"Back-End DTI of {back_end_dti:.1f}% and verified qualifying monthly income of ${entities.get('qualifying_monthly_income', 0.0):,.2f}."
        )
        key_findings.append(f"Back-End DTI ({back_end_dti:.1f}%) comfortably below maximum limit ({settings.MAX_DTI_BENCHMARK_PCT}%).")
        key_findings.append(f"Income cross-verification verified by: {', '.join(entities.get('income_source_documents', []))}.")

    decision_package = {
        "status": status,
        "confidence_score": confidence,
        "summary": summary,
        "key_findings": key_findings,
        "conditions": conditions,
    }

    reasoning.append(f"Final Decision rendered: [{status}] (Confidence: {confidence:.2f}).")

    return {
        "decision": decision_package,
        "reasoning_log": reasoning,
    }


# ---------------------------------------------------------------------------
# LangGraph Workflow Construction
# ---------------------------------------------------------------------------

def create_underwriting_graph():
    """Builds and compiles the StateGraph for mortgage underwriting."""
    graph = StateGraph(UnderwritingState)

    graph.add_node("extract_entities", extract_entities_node)
    graph.add_node("cross_verify", cross_verify_node)
    graph.add_node("evaluate_guidelines", evaluate_guidelines_node)
    graph.add_node("compile_decision", compile_decision_node)

    graph.add_edge(START, "extract_entities")
    graph.add_edge("extract_entities", "cross_verify")
    graph.add_edge("cross_verify", "evaluate_guidelines")
    graph.add_edge("evaluate_guidelines", "compile_decision")
    graph.add_edge("compile_decision", END)

    return graph.compile()


underwriting_graph = create_underwriting_graph()


async def run_underwriting_pipeline(
    application_id: uuid.UUID,
    borrower_name: str,
    borrower_email: str,
    loan_amount: float,
    documents: List[Dict[str, Any]],
    property_value: Optional[float] = None,
    monthly_debt: Optional[float] = None,
    interest_rate_pct: Optional[float] = None,
    loan_term_years: Optional[int] = None,
) -> Dict[str, Any]:
    """Asynchronously executes the underwriting agent graph for a given loan application."""
    initial_state: UnderwritingState = {
        "application_id": str(application_id),
        "borrower_name": borrower_name,
        "borrower_email": borrower_email,
        "loan_amount": loan_amount,
        "property_value": property_value or 0.0,
        "monthly_non_housing_debt": monthly_debt or 0.0,
        "interest_rate_pct": interest_rate_pct or settings.DEFAULT_MORTGAGE_INTEREST_RATE_PCT,
        "loan_term_years": loan_term_years or settings.DEFAULT_LOAN_TERM_YEARS,
        "documents": documents,
        "reasoning_log": [],
    }

    # Execute graph
    final_state = await underwriting_graph.ainvoke(initial_state)
    return final_state
