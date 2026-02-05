import { useState, useEffect } from 'react';
import './index.css';

const API_BASE = 'http://localhost:8000';

function formatCurrency(value) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

function formatPercent(value) {
  return `${value.toFixed(2)}%`;
}

// Step Indicator Component
function StepIndicator({ currentStep }) {
  const steps = [
    { number: 1, label: 'Upload Documents' },
    { number: 2, label: 'Review & Edit' },
    { number: 3, label: 'View Results' },
  ];

  return (
    <div className="step-indicator">
      {steps.map((step, index) => (
        <div key={step.number} style={{ display: 'flex', alignItems: 'center' }}>
          <div className={`step ${currentStep === step.number ? 'active' : ''} ${currentStep > step.number ? 'completed' : ''}`}>
            <div className="step-number">
              {currentStep > step.number ? '✓' : step.number}
            </div>
            <span className="step-label">{step.label}</span>
          </div>
          {index < steps.length - 1 && (
            <div className={`step-connector ${currentStep > step.number ? 'completed' : ''}`} />
          )}
        </div>
      ))}
    </div>
  );
}

// Document Upload Component
function DocumentUpload({ uploadedDocs, setUploadedDocs, onNext, formData, setFormData }) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const files = Array.from(e.dataTransfer.files);
    await uploadFiles(files);
  };

  const handleFileSelect = async (e) => {
    const files = Array.from(e.target.files);
    await uploadFiles(files);
  };

  const uploadFiles = async (files) => {
    setIsUploading(true);
    for (const file of files) {
      if (file.type !== 'application/pdf') continue;

      const formData = new FormData();
      formData.append('file', file);

      try {
        const response = await fetch(`${API_BASE}/api/upload`, {
          method: 'POST',
          body: formData,
        });

        if (response.ok) {
          const result = await response.json();
          setUploadedDocs(prev => [...prev, {
            id: Date.now() + Math.random(),
            filename: file.name,
            ...result,
          }]);
        }
      } catch (error) {
        console.error('Upload failed:', error);
      }
    }
    setIsUploading(false);
  };

  const removeDoc = (id) => {
    setUploadedDocs(prev => prev.filter(doc => doc.id !== id));
  };

  const getFormIcon = (formType) => {
    const icons = {
      'W-2': '📄',
      '1099-INT': '💰',
      '1099-DIV': '📈',
      '1099-B': '📊',
      '1099-NEC': '💼',
    };
    return icons[formType] || '📋';
  };

  const getFormClass = (formType) => {
    const classes = {
      'W-2': 'w2',
      '1099-INT': 'int',
      '1099-DIV': 'div',
      '1099-B': 'b',
      '1099-NEC': 'nec',
    };
    return classes[formType] || '';
  };

  return (
    <div className="fade-in">
      <div className="card">
        <div className="card-header">
          <div className="card-icon">📁</div>
          <div style={{ flex: 1 }}>
            <h2 className="card-title">Upload Tax Documents</h2>
            <p className="card-description">
              Upload your W-2, 1099-INT, 1099-DIV, 1099-B, or 1099-NEC forms
            </p>
          </div>
          <div className="tax-year-selector">
            <select
              value={formData.tax_year}
              onChange={(e) => setFormData({ ...formData, tax_year: parseInt(e.target.value) })}
              className="form-control"
              style={{ width: 'auto', fontWeight: 'bold' }}
            >
              <option value={2024}>Tax Year 2024</option>
              <option value={2025}>Tax Year 2025</option>
            </select>
          </div>
        </div>

        <div
          className={`upload-zone ${isDragOver ? 'drag-over' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => document.getElementById('file-input').click()}
        >
          <input
            id="file-input"
            type="file"
            accept=".pdf"
            multiple
            style={{ display: 'none' }}
            onChange={handleFileSelect}
          />
          <div className="upload-zone-icon">
            {isUploading ? '⏳' : '📤'}
          </div>
          <p className="upload-zone-title">
            {isUploading ? 'Uploading...' : 'Drop PDF files here or click to browse'}
          </p>
          <p className="upload-zone-subtitle">
            Supports W-2, 1099-INT, 1099-DIV, 1099-B, 1099-NEC
          </p>
        </div>

        {uploadedDocs.length > 0 && (
          <div className="uploaded-files">
            {uploadedDocs.map(doc => (
              <div key={doc.id} className="uploaded-file">
                <div className={`file-icon ${getFormClass(doc.form_type)}`}>
                  {getFormIcon(doc.form_type)}
                </div>
                <div className="file-info">
                  <div className="file-name">{doc.filename}</div>
                  <div className="file-type">Detected: {doc.form_type}</div>
                </div>
                <span className={`file-confidence ${doc.parse_confidence}`}>
                  {doc.parse_confidence}
                </span>
                <button className="file-remove" onClick={() => removeDoc(doc.id)}>
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="btn-group">
          <button className="btn btn-secondary" onClick={onNext}>
            Skip to Manual Entry →
          </button>
          {uploadedDocs.length > 0 && (
            <button className="btn btn-primary btn-lg" onClick={onNext}>
              Continue with {uploadedDocs.length} document{uploadedDocs.length > 1 ? 's' : ''} →
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// Income Review/Edit Component
function IncomeReview({ uploadedDocs, formData, setFormData, onBack, onCalculate, isCalculating }) {
  // Aggregate data from uploaded docs into form when component mounts or docs change
  useEffect(() => {
    if (uploadedDocs.length > 0) {
      const aggregated = {
        tax_year: formData.tax_year, // Preserve selected tax year
        w2_wages: 0,
        w2_federal_withheld: 0,
        w2_state_withheld: 0,
        w2_social_security_wages: 0,
        w2_casdi: 0,  // California State Disability Insurance
        interest_income: 0,
        interest_federal_withheld: 0,
        ordinary_dividends: 0,
        qualified_dividends: 0,
        capital_gain_distributions: 0,
        dividend_federal_withheld: 0,
        short_term_gains: 0,
        long_term_gains: 0,
        self_employment_income: 0,
        self_employment_federal_withheld: 0,
        estimated_tax_payments: 0,
        other_withholding: 0,
      };

      uploadedDocs.forEach(doc => {
        // The API returns parsed data in the 'data' property
        const data = doc.data || {};
        console.log('Processing doc:', doc.form_type, data);

        // Wages (W-2)
        aggregated.w2_wages += data.wages || 0;
        aggregated.w2_federal_withheld += data.federal_tax_withheld || 0;
        aggregated.w2_state_withheld += data.state_tax_withheld || 0;
        aggregated.w2_social_security_wages += data.social_security_wages || 0;
        aggregated.w2_casdi += data.casdi || 0;

        // Interest (1099-INT)
        aggregated.interest_income += data.interest_income || 0;
        // Note: data.federal_tax_withheld is already added to w2_federal_withheld above.
        // We do NOT add specific withholding fields if they map to the same source key.
        // BUT if parser Outputs specific keys (like 'interest_federal_withheld'?), we use them.
        // Currently parsers output 'federal_tax_withheld'. So it's lumped into w2_federal_withheld.

        // Dividends (1099-DIV)
        aggregated.ordinary_dividends += data.ordinary_dividends || 0;
        aggregated.qualified_dividends += data.qualified_dividends || 0;
        aggregated.capital_gain_distributions += data.capital_gain_distributions || 0;

        // Gains (1099-B)
        aggregated.short_term_gains += data.short_term_gains || 0;
        aggregated.long_term_gains += data.long_term_gains || 0;

        // Self Employment (1099-NEC)
        aggregated.self_employment_income += data.nonemployee_compensation || data.self_employment_income || 0;

        // Other Payments (1040)
        aggregated.estimated_tax_payments += data.estimated_tax_payments || 0;
        aggregated.other_withholding += data.other_withholding || 0;
      });

      console.log('Aggregated Form Data:', aggregated);
      setFormData(aggregated);
    }
  }, [uploadedDocs, setFormData]);

  const handleChange = (field) => (e) => {
    const value = parseFloat(e.target.value) || 0;
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="fade-in">
      <div className="card">
        <div className="card-header">
          <div className="card-icon">✏️</div>
          <div>
            <h2 className="card-title">Review & Edit Income</h2>
            <p className="card-description">
              Verify extracted data or enter your tax information manually
            </p>
          </div>
        </div>

        {/* W-2 Section */}
        <div className="form-section">
          <h3 className="form-section-title">W-2 Wages</h3>
          <div className="form-grid">
            <div className="form-group">
              <label className="form-label">Box 1: Wages, tips, other compensation</label>
              <div className="input-prefix">
                <input
                  type="number"
                  className="form-input"
                  value={formData.w2_wages || ''}
                  onChange={handleChange('w2_wages')}
                  placeholder="0.00"
                />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Box 2: Federal income tax withheld</label>
              <div className="input-prefix">
                <input
                  type="number"
                  className="form-input"
                  value={formData.w2_federal_withheld || ''}
                  onChange={handleChange('w2_federal_withheld')}
                  placeholder="0.00"
                />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Box 17: State income tax withheld</label>
              <div className="input-prefix">
                <input
                  type="number"
                  className="form-input"
                  value={formData.w2_state_withheld || ''}
                  onChange={handleChange('w2_state_withheld')}
                  placeholder="0.00"
                />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Box 3: Social Security wages</label>
              <div className="input-prefix">
                <input
                  type="number"
                  className="form-input"
                  value={formData.w2_social_security_wages || ''}
                  onChange={handleChange('w2_social_security_wages')}
                  placeholder="0.00"
                />
              </div>
            </div>
          </div>
        </div>

        {/* 1099-INT Section */}
        <div className="form-section">
          <h3 className="form-section-title">Interest Income (1099-INT)</h3>
          <div className="form-grid">
            <div className="form-group">
              <label className="form-label">Box 1: Interest income</label>
              <div className="input-prefix">
                <input
                  type="number"
                  className="form-input"
                  value={formData.interest_income || ''}
                  onChange={handleChange('interest_income')}
                  placeholder="0.00"
                />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Box 4: Federal tax withheld</label>
              <div className="input-prefix">
                <input
                  type="number"
                  className="form-input"
                  value={formData.interest_federal_withheld || ''}
                  onChange={handleChange('interest_federal_withheld')}
                  placeholder="0.00"
                />
              </div>
            </div>
          </div>
        </div>

        {/* 1099-DIV Section */}
        <div className="form-section">
          <h3 className="form-section-title">Dividend Income (1099-DIV)</h3>
          <div className="form-grid">
            <div className="form-group">
              <label className="form-label">Box 1a: Total ordinary dividends</label>
              <div className="input-prefix">
                <input
                  type="number"
                  className="form-input"
                  value={formData.ordinary_dividends || ''}
                  onChange={handleChange('ordinary_dividends')}
                  placeholder="0.00"
                />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Box 1b: Qualified dividends</label>
              <div className="input-prefix">
                <input
                  type="number"
                  className="form-input"
                  value={formData.qualified_dividends || ''}
                  onChange={handleChange('qualified_dividends')}
                  placeholder="0.00"
                />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Box 2a: Capital gain distributions</label>
              <div className="input-prefix">
                <input
                  type="number"
                  className="form-input"
                  value={formData.capital_gain_distributions || ''}
                  onChange={handleChange('capital_gain_distributions')}
                  placeholder="0.00"
                />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Box 4: Federal tax withheld</label>
              <div className="input-prefix">
                <input
                  type="number"
                  className="form-input"
                  value={formData.dividend_federal_withheld || ''}
                  onChange={handleChange('dividend_federal_withheld')}
                  placeholder="0.00"
                />
              </div>
            </div>
          </div>
        </div>

        {/* 1099-B Section */}
        <div className="form-section">
          <h3 className="form-section-title">Capital Gains/Losses (1099-B)</h3>
          <div className="form-grid">
            <div className="form-group">
              <label className="form-label">Short-term gain/loss (held ≤ 1 year)</label>
              <div className="input-prefix">
                <input
                  type="number"
                  className="form-input"
                  value={formData.short_term_gains || ''}
                  onChange={handleChange('short_term_gains')}
                  placeholder="0.00"
                />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Long-term gain/loss (held &gt; 1 year)</label>
              <div className="input-prefix">
                <input
                  type="number"
                  className="form-input"
                  value={formData.long_term_gains || ''}
                  onChange={handleChange('long_term_gains')}
                  placeholder="0.00"
                />
              </div>
            </div>
          </div>
        </div>

        {/* 1099-NEC Section */}
        <div className="form-section">
          <h3 className="form-section-title">Self-Employment Income (1099-NEC)</h3>
          <div className="form-grid">
            <div className="form-group">
              <label className="form-label">Box 1: Nonemployee compensation</label>
              <div className="input-prefix">
                <input
                  type="number"
                  className="form-input"
                  value={formData.self_employment_income || ''}
                  onChange={handleChange('self_employment_income')}
                  placeholder="0.00"
                />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Box 4: Federal tax withheld</label>
              <div className="input-prefix">
                <input
                  type="number"
                  className="form-input"
                  value={formData.self_employment_federal_withheld || ''}
                  onChange={handleChange('self_employment_federal_withheld')}
                  placeholder="0.00"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Other Payments Section (1040) */}
        <div className="form-section">
          <h3 className="form-section-title">Other Payments & Credits</h3>
          <div className="form-grid">
            <div className="form-group">
              <label className="form-label">Estimated Tax Payments</label>
              <div className="input-prefix">
                <input
                  type="number"
                  className="form-input"
                  value={formData.estimated_tax_payments || ''}
                  onChange={handleChange('estimated_tax_payments')}
                  placeholder="0.00"
                />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Other Federal Withholding</label>
              <div className="input-prefix">
                <input
                  type="number"
                  className="form-input"
                  value={formData.other_withholding || ''}
                  onChange={handleChange('other_withholding')}
                  placeholder="0.00"
                />
              </div>
            </div>
          </div>
        </div>

        <div className="btn-group">
          <button className="btn btn-secondary" onClick={onBack}>
            ← Back
          </button>
          <button
            className="btn btn-primary btn-lg"
            onClick={onCalculate}
            disabled={isCalculating}
          >
            {isCalculating ? 'Calculating...' : 'Calculate Taxes →'}
          </button>
        </div>
      </div>
    </div>
  );
}

// Tax Results Component
function TaxResults({ results, onBack, onStartOver }) {
  if (!results) return null;

  const isRefund = results.amount_owed < 0;
  const bottomLineAmount = Math.abs(results.amount_owed);

  // Calculate federal and state owed/refund separately
  const federalOwed = results.federal.total_federal_tax - results.total_federal_withheld;
  const stateOwed = results.california.total_california_tax - results.total_state_withheld;

  return (
    <div className="fade-in">
      {/* Summary Card */}
      <div className="summary-card">
        <p className="summary-label">
          {isRefund ? 'Estimated Refund' : 'Estimated Amount Owed'}
        </p>
        <p className={`summary-amount ${isRefund ? 'refund' : 'owed'}`}>
          {formatCurrency(bottomLineAmount)}
        </p>

        {/* Federal and State Breakdown */}
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          gap: 'var(--space-xl)',
          marginTop: 'var(--space-md)',
          flexWrap: 'wrap'
        }}>
          <div style={{ textAlign: 'center' }}>
            <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>🇺🇸 Federal</span>
            <p style={{
              fontSize: '1.25rem',
              fontWeight: 600,
              color: federalOwed >= 0 ? 'var(--danger)' : 'var(--success)',
              margin: '0.25rem 0 0 0'
            }}>
              {federalOwed >= 0 ? 'Owe ' : 'Refund '}{formatCurrency(Math.abs(federalOwed))}
            </p>
          </div>
          <div style={{ textAlign: 'center' }}>
            <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>🐻 California</span>
            <p style={{
              fontSize: '1.25rem',
              fontWeight: 600,
              color: stateOwed >= 0 ? 'var(--danger)' : 'var(--success)',
              margin: '0.25rem 0 0 0'
            }}>
              {stateOwed >= 0 ? 'Owe ' : 'Refund '}{formatCurrency(Math.abs(stateOwed))}
            </p>
          </div>
        </div>

        <p className="summary-note" style={{ marginTop: 'var(--space-md)' }}>
          Based on {results.tax_year || 2024} federal and California tax rates • Filing Single • Standard Deduction
        </p>
      </div>

      {/* Income Summary */}
      <div className="results-grid">
        <div className="result-card">
          <div className="result-card-header">
            <span className="result-card-title">Gross Income</span>
          </div>
          <p className="result-card-value">{formatCurrency(results.gross_income)}</p>
        </div>

        <div className="result-card">
          <div className="result-card-header">
            <span className="result-card-title">Total Tax Withheld</span>
          </div>
          <p className="result-card-value">{formatCurrency(results.total_withheld)}</p>
          <p className="result-card-subtitle">
            Federal: {formatCurrency(results.total_federal_withheld)} • State: {formatCurrency(results.total_state_withheld)}
          </p>
        </div>

        <div className="result-card">
          <div className="result-card-header">
            <span className="result-card-title">Total Tax Liability</span>
          </div>
          <p className="result-card-value">{formatCurrency(results.total_tax_liability)}</p>
        </div>
      </div>

      {/* Federal Tax Breakdown */}
      <div className="card" style={{ marginBottom: 'var(--space-lg)' }}>
        <div className="card-header">
          <div className="card-icon">🇺🇸</div>
          <div>
            <h2 className="card-title">Federal Tax Breakdown</h2>
            <p className="card-description">
              Effective Rate: {formatPercent(results.federal.effective_rate)} •
              Marginal Rate: {formatPercent(results.federal.marginal_rate)}
            </p>
          </div>
        </div>

        <table className="breakdown-table">
          <thead>
            <tr>
              <th>Description</th>
              <th style={{ textAlign: 'right' }}>Amount</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Gross Income</td>
              <td style={{ textAlign: 'right' }}>{formatCurrency(results.federal.gross_income)}</td>
            </tr>
            <tr>
              <td>Standard Deduction (Single)</td>
              <td style={{ textAlign: 'right' }}>-{formatCurrency(results.federal.standard_deduction)}</td>
            </tr>
            <tr>
              <td>Federal Taxable Income</td>
              <td style={{ textAlign: 'right' }}>{formatCurrency(results.federal.taxable_income)}</td>
            </tr>
            <tr>
              <td>Ordinary Income Tax</td>
              <td style={{ textAlign: 'right' }}>{formatCurrency(results.federal.ordinary_income_tax)}</td>
            </tr>
            {results.federal.capital_gains_tax > 0 && (
              <tr>
                <td>Capital Gains Tax</td>
                <td style={{ textAlign: 'right' }}>{formatCurrency(results.federal.capital_gains_tax)}</td>
              </tr>
            )}
            {results.federal.self_employment_tax > 0 && (
              <tr>
                <td>Self-Employment Tax</td>
                <td style={{ textAlign: 'right' }}>{formatCurrency(results.federal.self_employment_tax)}</td>
              </tr>
            )}
            <tr className="total-row">
              <td><strong>Total Federal Tax</strong></td>
              <td style={{ textAlign: 'right' }}><strong>{formatCurrency(results.federal.total_federal_tax)}</strong></td>
            </tr>
          </tbody>
        </table>

        {results.federal.bracket_breakdown?.length > 0 && (
          <>
            <h4 style={{ marginTop: 'var(--space-lg)', marginBottom: 'var(--space-sm)', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
              Tax Bracket Breakdown
            </h4>
            <table className="breakdown-table">
              <thead>
                <tr>
                  <th>Bracket</th>
                  <th>Rate</th>
                  <th style={{ textAlign: 'right' }}>Income</th>
                  <th style={{ textAlign: 'right' }}>Tax</th>
                </tr>
              </thead>
              <tbody>
                {results.federal.bracket_breakdown.map((bracket, i) => (
                  <tr key={i}>
                    <td>{formatCurrency(bracket.range_start)} - {formatCurrency(bracket.range_end)}</td>
                    <td>{formatPercent(bracket.rate * 100)}</td>
                    <td style={{ textAlign: 'right' }}>{formatCurrency(bracket.income_in_bracket)}</td>
                    <td style={{ textAlign: 'right' }}>{formatCurrency(bracket.tax_in_bracket)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}
      </div>

      {/* California Tax Breakdown */}
      <div className="card" style={{ marginBottom: 'var(--space-lg)' }}>
        <div className="card-header">
          <div className="card-icon">🐻</div>
          <div>
            <h2 className="card-title">California Tax Breakdown</h2>
            <p className="card-description">
              Effective Rate: {formatPercent(results.california.effective_rate)} •
              Marginal Rate: {formatPercent(results.california.marginal_rate)}
            </p>
          </div>
        </div>

        <table className="breakdown-table">
          <thead>
            <tr>
              <th>Description</th>
              <th style={{ textAlign: 'right' }}>Amount</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Gross Income</td>
              <td style={{ textAlign: 'right' }}>{formatCurrency(results.california.gross_income)}</td>
            </tr>
            <tr>
              <td>Standard Deduction (Single)</td>
              <td style={{ textAlign: 'right' }}>-{formatCurrency(results.california.standard_deduction)}</td>
            </tr>
            <tr>
              <td>California Taxable Income</td>
              <td style={{ textAlign: 'right' }}>{formatCurrency(results.california.taxable_income)}</td>
            </tr>
            <tr>
              <td>State Income Tax</td>
              <td style={{ textAlign: 'right' }}>{formatCurrency(results.california.state_tax)}</td>
            </tr>
            {results.california.mental_health_surcharge > 0 && (
              <tr>
                <td>Mental Health Services Tax</td>
                <td style={{ textAlign: 'right' }}>{formatCurrency(results.california.mental_health_surcharge)}</td>
              </tr>
            )}
            <tr className="total-row">
              <td><strong>Total California Tax</strong></td>
              <td style={{ textAlign: 'right' }}><strong>{formatCurrency(results.california.total_california_tax)}</strong></td>
            </tr>
          </tbody>
        </table>
      </div>

      <div className="btn-group">
        <button className="btn btn-secondary" onClick={onBack}>
          ← Edit Income
        </button>
        <button className="btn btn-primary" onClick={onStartOver}>
          Start Over
        </button>
      </div>
    </div>
  );
}

// Main App Component
function App() {
  const [step, setStep] = useState(1);
  const [uploadedDocs, setUploadedDocs] = useState([]);
  const [formData, setFormData] = useState({
    tax_year: 2024,
    w2_wages: 0,
    w2_federal_withheld: 0,
    w2_state_withheld: 0,
    w2_social_security_wages: 0,
    w2_casdi: 0,  // California State Disability Insurance
    interest_income: 0,
    interest_federal_withheld: 0,
    ordinary_dividends: 0,
    qualified_dividends: 0,
    capital_gain_distributions: 0,
    dividend_federal_withheld: 0,
    short_term_gains: 0,
    long_term_gains: 0,
    self_employment_income: 0,
    self_employment_federal_withheld: 0,
  });
  const [results, setResults] = useState(null);
  const [isCalculating, setIsCalculating] = useState(false);

  const handleCalculate = async () => {
    setIsCalculating(true);
    try {
      const response = await fetch(`${API_BASE}/api/calculate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        const data = await response.json();
        setResults(data);
        setStep(3);
      }
    } catch (error) {
      console.error('Calculation failed:', error);
    }
    setIsCalculating(false);
  };

  const handleStartOver = () => {
    setStep(1);
    setUploadedDocs([]);
    setFormData({
      tax_year: 2024,
      w2_wages: 0,
      w2_federal_withheld: 0,
      w2_state_withheld: 0,
      w2_social_security_wages: 0,
      w2_casdi: 0,
      interest_income: 0,
      interest_federal_withheld: 0,
      ordinary_dividends: 0,
      qualified_dividends: 0,
      capital_gain_distributions: 0,
      dividend_federal_withheld: 0,
      short_term_gains: 0,
      long_term_gains: 0,
      self_employment_income: 0,
      self_employment_federal_withheld: 0,
    });
    setResults(null);
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <div className="app-logo">
            <span style={{ fontSize: '1.75rem' }}>🧮</span>
            <div>
              <h1 className="app-title">Tax Calculator 2025</h1>
              <p className="app-subtitle">Federal & California • Single Filer</p>
            </div>
          </div>
        </div>
      </header>

      <main className="main-content">
        <StepIndicator currentStep={step} />

        {step === 1 && (
          <DocumentUpload
            uploadedDocs={uploadedDocs}
            setUploadedDocs={setUploadedDocs}
            onNext={() => setStep(2)}
            formData={formData}
            setFormData={setFormData}
          />
        )}

        {step === 2 && (
          <IncomeReview
            uploadedDocs={uploadedDocs}
            formData={formData}
            setFormData={setFormData}
            onBack={() => setStep(1)}
            onCalculate={handleCalculate}
            isCalculating={isCalculating}
          />
        )}

        {step === 3 && (
          <TaxResults
            results={results}
            onBack={() => setStep(2)}
            onStartOver={handleStartOver}
          />
        )}
      </main>
    </div>
  );
}

export default App;
