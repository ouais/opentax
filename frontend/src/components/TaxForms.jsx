import React, { useState } from 'react';
import './TaxForms.css';

const formatMoney = (val) => {
    if (val === undefined || val === null) return '';
    return val.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};

// Form 1040 Component
const Form1040 = ({ info, data, withholding, estimatedPayments, otherWithholding, amountOwed }) => {
    // Calculated fields for display
    const totalPayments = (withholding || 0) + (estimatedPayments || 0) + (otherWithholding || 0);
    const refund = totalPayments > (data.total_federal_tax || 0) ? totalPayments - data.total_federal_tax : 0;
    // If amountOwed is passed, use it, otherwise calc
    const owed = amountOwed !== undefined ? amountOwed : (data.total_federal_tax > totalPayments ? data.total_federal_tax - totalPayments : 0);

    return (
        <div className="tax-form-page">
            <div className="tf-header">
                <div className="tf-header-left">1040</div>
                <div className="tf-header-center">
                    <div className="tf-header-title">U.S. Individual Income Tax Return</div>
                    <div className="tf-header-year">2025</div>
                </div>
                <div className="tf-header-right">
                    Department of the Treasury<br />Internal Revenue Service
                </div>
            </div>

            <div className="tf-pii-grid">
                <div className="tf-pii-field">
                    <span className="tf-grid-label">First Name and Initial</span>
                    <div className="tf-grid-value">{info.firstName}</div>
                </div>
                <div className="tf-pii-field">
                    <span className="tf-grid-label">Last Name</span>
                    <div className="tf-grid-value">{info.lastName}</div>
                </div>
                <div className="tf-pii-field" style={{ gridColumn: 'span 2' }}>
                    <span className="tf-grid-label">Home Address (number and street)</span>
                    <div className="tf-grid-value">{info.address}</div>
                </div>
                <div className="tf-pii-field">
                    <span className="tf-grid-label">City, town or post office</span>
                    <div className="tf-grid-value">{info.city}</div>
                </div>
                <div className="tf-pii-field">
                    <span className="tf-grid-label">State & ZIP</span>
                    <div className="tf-grid-value">{info.state} {info.zip}</div>
                </div>
                <div className="tf-pii-field">
                    <span className="tf-grid-label">Your Social Security Number</span>
                    <div className="tf-grid-value">{info.ssn}</div>
                </div>
            </div>

            <div className="tf-section-header">Income</div>

            <FormLine num="1z" desc="Wages, salaries, tips, etc." val={data.wages} />
            <FormLine num="2b" desc="Taxable interest" val={data.interest_income} />
            <FormLine num="3a" desc="Qualified dividends" val={data.qualified_dividends} />
            <FormLine num="3b" desc="Ordinary dividends" val={data.total_ordinary_dividends} />
            <FormLine num="7" desc="Capital gain or (loss)" val={data.capital_gains} />
            <FormLine num="8" desc="Other income (Schedule 1)" val={0} />
            <FormLine num="9" desc="Total income. Add lines 1z, 2b, 3b, 4b, 5b, 6b, 7, and 8" val={data.total_income} bold />

            <FormLine num="10" desc="Adjustments to income" val={0} />
            <FormLine num="11" desc="Adjusted Gross Income. Subtract line 10 from line 9" val={data.adjusted_gross_income} bold />

            <FormLine num="12" desc="Standard deduction or itemized deductions" val={data.standard_deduction} />
            <FormLine num="13" desc="Qualified business income deduction" val={0} />
            <FormLine num="14" desc="Add lines 12 and 13" val={data.standard_deduction} />
            <FormLine num="15" desc="Taxable income. Subtract line 14 from line 11" val={data.taxable_income} bold />

            <div className="tf-section-header">Tax and Credits</div>
            <FormLine num="16" desc="Tax (see instructions)" val={(data.ordinary_income_tax || 0) + (data.capital_gains_tax || 0)} />
            <FormLine num="23" desc="Other taxes (Schedule 2)" val={(data.self_employment_tax || 0) + (data.additional_medicare_tax || 0)} />
            <FormLine num="24" desc="Total Tax. Add lines 22 and 23" val={data.total_federal_tax} bold />

            <div className="tf-section-header">Payments</div>
            <FormLine num="25d" desc="Federal income tax withheld" val={withholding} />
            <FormLine num="26" desc="2024 estimated tax payments and amount applied from 2023 return" val={estimatedPayments} />
            {otherWithholding > 0 && <FormLine num="25c" desc="Other withholding" val={otherWithholding} />}
            <FormLine num="33" desc="Total payments. Add lines 25d, 26, and 32" val={totalPayments} bold />

            <div className="tf-section-header">Refund</div>
            <FormLine num="34" desc="If line 33 is more than line 24, subtract line 24 from line 33" val={refund > 0 ? refund : 0} />

            <div className="tf-section-header">Amount You Owe</div>
            <FormLine num="37" desc="Amount you owe. Subtract line 33 from line 24" val={owed > 0 ? owed : 0} bold />

            <div style={{ marginTop: '20px', textAlign: 'center', fontSize: '10px' }}>
                * Calculated by OpenTax. Not an official IRS form.
            </div>
        </div>
    );
};

// Form 540 Component (California)
const Form540 = ({ info, data, fedAGI }) => {
    // Note: data is results.california

    // Need to correctly display CA withholding (Wait, data.state_tax is TAX. What is WITHHOLDING?)
    // Passed in props.
    // CA Logic:
    // Taxable Income = Gross - Standard Ded.
    // Tax = State Tax + Mental Health.
    // Payments = Withholding.

    // We need 'total_state_withheld' from the calculation result wrapper, NOT just the 'california' key.
    // So Parent must pass 'stateWithholding'.

    // Wait, info is PII. withholding should be a prop.

    return (
        <div className="tax-form-page">
            <div className="tf-header ca-header">
                <div className="tf-header-left">FORM 540</div>
                <div className="tf-header-center">
                    <div className="tf-header-title">California Resident Income Tax Return</div>
                    <div className="tf-header-year">2025</div>
                </div>
                <div className="tf-header-right">
                    Fiscal year beginning<br />Fiscal year ending
                </div>
            </div>

            <div className="tf-pii-grid">
                <div className="tf-pii-field" style={{ gridColumn: 'span 2' }}>
                    <span className="tf-grid-label">Your Name</span>
                    <div className="tf-grid-value">{info.firstName} {info.lastName}</div>
                </div>
                <div className="tf-pii-field">
                    <span className="tf-grid-label">SSN</span>
                    <div className="tf-grid-value">{info.ssn}</div>
                </div>
                <div className="tf-pii-field" style={{ gridColumn: 'span 2' }}>
                    <span className="tf-grid-label">Address</span>
                    <div className="tf-grid-value">{info.address} {info.city} {info.state} {info.zip}</div>
                </div>
            </div>

            <div className="tf-section-header">Taxable Income</div>
            <FormLine num="13" desc="Federal Adjusted Gross Income (Form 1040, line 11)" val={fedAGI} />
            <FormLine num="14" desc="California Adjustments - Subtractions (Schedule CA)" val={0} />
            <FormLine num="15" desc="Subtract line 14 from line 13" val={data.gross_income} />
            <FormLine num="18" desc="California Adjusted Gross Income" val={data.gross_income} bold />

            <FormLine num="19" desc="Standard Deduction" val={data.standard_deduction} />
            <FormLine num="31" desc="Taxable Income. Subtract line 19 from line 18" val={data.taxable_income} bold />

            <div className="tf-section-header">Tax using Tax Rate Table</div>
            <FormLine num="31" desc="Tax on line 19 amount" val={data.state_tax} />
            <FormLine num="35" desc="Total Tax" val={data.state_tax} />

            <div className="tf-section-header">Special Taxes</div>
            <FormLine num="61" desc="Mental Health Services Tax" val={data.mental_health_surcharge} />
            <FormLine num="64" desc="Total Tax. Add line 35 and line 61" val={data.total_california_tax} bold />

            <div className="tf-section-header">Payments</div>
            <FormLine num="71" desc="California Income Tax Withheld (Form W-2, 1099)" val={info.stateWithholding} />
            <FormLine num="75" desc="Total Payments" val={info.stateWithholding} bold />

            <div className="tf-section-header">Amount You Owe / Refund</div>
            {/* Logic for Refund/Owe */}
            {(info.stateWithholding > data.total_california_tax) ? (
                <FormLine num="96" desc="Refund. Subtract line 64 from line 75" val={info.stateWithholding - data.total_california_tax} bold />
            ) : (
                <FormLine num="111" desc="Amount You Owe. Subtract line 75 from line 64" val={data.total_california_tax - info.stateWithholding} bold />
            )}

            <div style={{ marginTop: '20px', textAlign: 'center', fontSize: '10px' }}>
                * Calculated by OpenTax. Not an official FTB form.
            </div>
        </div>
    );
};

// Helper Line Component
const FormLine = ({ num, desc, val, bold = false }) => (
    <div className={`tf-row ${bold ? 'major' : ''}`}>
        <div className="tf-line-num">{num}</div>
        <div className="tf-desc" style={{ fontWeight: bold ? 'bold' : 'normal' }}>{desc}</div>
        <div className="tf-inputs">
            <div className="tf-input-box" style={{ fontWeight: bold ? 'bold' : 'normal' }}>
                {formatMoney(val)}
            </div>
        </div>
    </div>
);

// Main Container
export default function TaxForms({ results, formData }) {
    const [pii, setPii] = useState({
        firstName: '',
        lastName: '',
        ssn: '',
        address: '',
        city: '',
        state: '',
        zip: '',
    });

    // Calculate total state withholding based on formData passed from App
    // Note: we removed CASDI from backend calc.
    // Frontend formData aggregation (Step 819) has w2_state_withheld separately.
    // But Results (Step 808) contains total_state_withheld.
    // But Results (Step 808) contains total_state_withheld.

    const handlePiiChange = (field) => (e) => {
        setPii({ ...pii, [field]: e.target.value });
    };

    const handleDownloadPdf = async (formType = 'all') => {
        try {
            // Sanitize formData to ensure numbers (same as App.jsx handleCalculate)
            // Robust helper to prevent null/NaN
            const safeNum = (v) => {
                if (v === null || v === undefined || v === '') return 0;
                const n = Number(v);
                return isNaN(n) ? 0 : n;
            };

            const sanitizedData = {
                w2_wages: safeNum(formData.w2_wages),
                w2_federal_withheld: safeNum(formData.w2_federal_withheld),
                w2_state_withheld: safeNum(formData.w2_state_withheld),
                w2_social_security_wages: safeNum(formData.w2_social_security_wages),
                w2_medicare_wages: safeNum(formData.w2_medicare_wages),
                w2_medicare_tax: safeNum(formData.w2_medicare_tax),
                w2_casdi: safeNum(formData.w2_casdi),
                interest_income: safeNum(formData.interest_income),
                interest_federal_withheld: safeNum(formData.interest_federal_withheld),
                ordinary_dividends: safeNum(formData.ordinary_dividends),
                qualified_dividends: safeNum(formData.qualified_dividends),
                capital_gain_distributions: safeNum(formData.capital_gain_distributions),
                dividend_federal_withheld: safeNum(formData.dividend_federal_withheld),
                short_term_gains: safeNum(formData.short_term_gains),
                long_term_gains: safeNum(formData.long_term_gains),
                self_employment_income: safeNum(formData.self_employment_income),
                self_employment_federal_withheld: safeNum(formData.self_employment_federal_withheld),
                estimated_tax_payments: safeNum(formData.estimated_tax_payments),
                other_withholding: safeNum(formData.other_withholding),
                itemized_deductions: safeNum(formData.itemized_deductions),
                foreign_income: safeNum(formData.foreign_income),
                tax_year: parseInt(formData.tax_year) || 2024,
                filing_status: String(formData.filing_status || 'single'),
                state: String(formData.state || 'CA'),
            };

            // Add timestamp to prevent caching
            // Use API_BASE to point to the backend server (e.g. localhost:8000)
            const API_BASE = 'http://localhost:8000';
            const response = await fetch(`${API_BASE}/api/generate-pdf?form_type=${formType}&t=${Date.now()}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ...sanitizedData, pii })
            });
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                const filenames = {
                    '1040': 'form1040_2025.pdf',
                    '540': 'ca540_2025.pdf',
                    'all': 'tax_forms_2025.zip',
                };
                a.download = filenames[formType] || 'tax_forms_2025.zip';
                document.body.appendChild(a);
                a.click();
                a.remove();
            } else {
                console.error('PDF Generation Failed', response.status, response.statusText);
                const errorText = await response.text();
                console.error('Error Details:', errorText);

                if (response.status === 422) {
                    alert('Data error detected. Refreshing app to fix...');
                    window.location.reload(true); // Force reload to clear stale code/state
                } else {
                    alert('Failed to generate PDF. Please try again.');
                }
            }
        } catch (e) {
            console.error(e);
            alert('Error generating PDF');
        }
    };

    if (!results) return <div>Please calculate taxes first.</div>;

    // ... logic ...

    return (
        <div className="tax-forms-container" style={{ maxWidth: '800px', margin: '0 auto' }}>
            <div className="card">
                <div style={{ display: 'flex', alignItems: 'center', gap: '15px', marginBottom: '24px' }}>
                    <div className="card-icon">PDF</div>
                    <div>
                        <h3 className="card-title">Generate Tax Forms</h3>
                        <p className="card-description">Enter your info to generate official value-filled PDFs for Federal (1040) and California (540).</p>
                    </div>
                </div>

                <div className="form-grid" style={{ marginBottom: '32px' }}>
                    <div className="form-group">
                        <label className="form-label">First Name</label>
                        <input className="form-input" value={pii.firstName} onChange={handlePiiChange('firstName')} placeholder="John" />
                    </div>
                    <div className="form-group">
                        <label className="form-label">Last Name</label>
                        <input className="form-input" value={pii.lastName} onChange={handlePiiChange('lastName')} placeholder="Doe" />
                    </div>
                    <div className="form-group">
                        <label className="form-label">SSN (Optional)</label>
                        <input className="form-input" value={pii.ssn} onChange={handlePiiChange('ssn')} placeholder="000-00-0000" />
                    </div>
                    <div className="form-group">
                        <label className="form-label">Street Address</label>
                        <input className="form-input" value={pii.address} onChange={handlePiiChange('address')} placeholder="123 Main St" />
                    </div>
                    <div className="form-group">
                        <label className="form-label">City</label>
                        <input className="form-input" value={pii.city} onChange={handlePiiChange('city')} placeholder="New York" />
                    </div>
                    <div className="form-group" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                        <div>
                            <label className="form-label">State</label>
                            <input className="form-input" value={pii.state} onChange={handlePiiChange('state')} placeholder="NY" />
                        </div>
                        <div>
                            <label className="form-label">ZIP</label>
                            <input className="form-input" value={pii.zip} onChange={handlePiiChange('zip')} placeholder="10001" />
                        </div>
                    </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    <button className="btn btn-primary btn-lg" onClick={() => handleDownloadPdf('all')} style={{ width: '100%', justifyContent: 'center' }}>
                        Download All Forms (ZIP)
                    </button>
                    <div style={{ display: 'flex', gap: '10px' }}>
                        <button className="btn btn-secondary" onClick={() => handleDownloadPdf('1040')} style={{ flex: 1, justifyContent: 'center' }}>
                            Form 1040 Only
                        </button>
                        <button className="btn btn-secondary" onClick={() => handleDownloadPdf('540')} style={{ flex: 1, justifyContent: 'center' }}>
                            CA 540 Only
                        </button>
                    </div>
                    <p className="summary-note" style={{ textAlign: 'center' }}>
                        Your data is processed locally and never stored on a server.
                    </p>
                </div>
            </div>
        </div>
    );
}
