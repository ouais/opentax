import { useState, useEffect } from 'react';
import './index.css';
import TaxForms from './components/TaxForms';

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

const FIELD_LABEL_PATTERNS = [
  'name line', 'street address', 'city or town', 'state or province',
  'zip code', 'postal code', 'taxpayer identification',
  'recipient', 'account number', 'fatca', 'form 1099', 'corrected',
  'omb no', 'department of', 'internal revenue', 'payer',
];

function getInstitutionName(doc) {
  const raw = doc.data?.payer_name || doc.data?.employer_name || doc.data?.employer || doc.data?.payer || '';
  if (!raw) return '';
  const lower = raw.toLowerCase();
  if (FIELD_LABEL_PATTERNS.some(label => lower.includes(label))) return '';
  if ([...raw].filter(c => /\d/.test(c)).length / raw.length > 0.5) return '';
  return raw;
}

const STATE_CONFIG = {
  CA: { name: 'California' },
  NY: { name: 'New York' },
  TX: { name: 'Texas' },
  FL: { name: 'Florida' },
  WA: { name: 'Washington' },
  TN: { name: 'Tennessee' },
  NV: { name: 'Nevada' },
  SD: { name: 'South Dakota' },
  WY: { name: 'Wyoming' },
  AK: { name: 'Alaska' },
  NH: { name: 'New Hampshire' },
};

function getStateName(code) {
  return STATE_CONFIG[code]?.name || code;
}

function getStateIcon(code) {
  return code;
}

function getFormIcon(formType) {
  return formType.charAt(0);
}

function getFormClass(formType) {
  const classes = {
    'W-2': 'w2',
    '1099-INT': 'int',
    '1099-DIV': 'div',
    '1099-B': 'b',
    '1099-NEC': 'nec',
  };
  return classes[formType] || '';
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



  return (
    <div className="fade-in">
      <div className="card">
        <div className="card-header">
          <div className="card-icon">1</div>
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
              className="form-select"
              style={{ width: 'auto', fontWeight: 'bold' }}
            >
              <option value={2024}>Tax Year 2024</option>
              <option value={2025}>Tax Year 2025</option>
            </select>
          </div>
          <div className="state-selector" style={{ marginLeft: '10px' }}>
            <select
              value={formData.state || 'CA'}
              onChange={(e) => setFormData({ ...formData, state: e.target.value })}
              className="form-select"
              style={{ width: 'auto', fontWeight: 'bold' }}
            >
              <option value="CA">California</option>
              <option value="NY">New York</option>
              <option value="TX">Texas (No Income Tax)</option>
              <option value="FL">Florida</option>
              <option value="WA">Washington</option>
              <option value="TN">Tennessee</option>
              <option value="NV">Nevada</option>
              <option value="SD">South Dakota</option>
              <option value="WY">Wyoming</option>
              <option value="AK">Alaska</option>
              <option value="NH">New Hampshire</option>
            </select>
          </div>
          <div className="filing-status-selector" style={{ marginLeft: '10px' }}>
            <select
              value={formData.filing_status || 'single'}
              onChange={(e) => setFormData({ ...formData, filing_status: e.target.value })}
              className="form-select"
              style={{ width: 'auto', fontWeight: 'bold' }}
            >
              <option value="single">Single</option>
              <option value="joint">Married Filing Jointly</option>
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
            {isUploading ? '...' : '↑'}
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
                  <div className="file-type">
                    {doc.form_type}
                    {getInstitutionName(doc) && (
                      <span style={{ color: 'var(--text-secondary)', marginLeft: '8px' }}>
                        • {getInstitutionName(doc)}
                      </span>
                    )}
                  </div>
                </div>
                <span className={`file-confidence ${doc.parse_confidence}`}>
                  {doc.parse_confidence === 'high' ? 'Uploaded' :
                    doc.parse_confidence === 'medium' ? 'Review' : 'Check Data'}
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

        // Dividends (1099-DIV) — parser returns total_ordinary_dividends (Box 1a) and total_capital_gain_dist (Box 2a)
        aggregated.ordinary_dividends += data.total_ordinary_dividends || data.ordinary_dividends || 0;
        aggregated.qualified_dividends += data.qualified_dividends || 0;
        aggregated.capital_gain_distributions += data.total_capital_gain_dist || data.capital_gain_distributions || 0;

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
          <div className="card-icon">2</div>
          <div>
            <h2 className="card-title">Review & Edit Income</h2>
            <p className="card-description">
              Verify extracted data or enter your tax information manually
            </p>
          </div>
        </div>

        <div className="form-section" style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '20px' }}>
          <div className="form-grid">
            <div className="form-group">
              <label className="form-label">Filing Status</label>
              <select
                value={formData.filing_status || 'single'}
                onChange={(e) => setFormData({ ...formData, filing_status: e.target.value })}
                className="form-select"
              >
                <option value="single">Single</option>
                <option value="joint">Married Filing Jointly</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Tax Year</label>
              <select
                value={formData.tax_year}
                onChange={(e) => setFormData({ ...formData, tax_year: parseInt(e.target.value) })}
                className="form-select"
              >
                <option value={2024}>2024</option>
                <option value={2025}>2025</option>
              </select>
            </div>
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
function TaxResults({ results, state, uploadedDocs, onBack, onStartOver, onViewForms, onViewLaws }) {
  if (!results) return null;

  const isRefund = results.amount_owed < 0;
  const bottomLineAmount = Math.abs(results.amount_owed);

  // Calculate federal and state owed/refund separately
  const federalOwed = results.federal.total_federal_tax - results.total_federal_withheld;
  const stateOwed = results.california.total_california_tax - results.total_state_withheld;

  return (
    <div className="fade-in" style={{ display: 'grid', gridTemplateColumns: '300px 1fr 200px', gap: '24px', alignItems: 'start', padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>

      {/* LEFT COLUMN - Source Documents */}
      <div className="no-print" style={{ position: 'sticky', top: '90px' }}>
        <div className="card" style={{ padding: '16px' }}>
          <h3 className="card-title" style={{ fontSize: '1rem', marginBottom: '12px' }}>Source Documents</h3>
          {uploadedDocs && uploadedDocs.length > 0 ? (
            <div>
              {uploadedDocs.map(doc => (
                <div key={doc.id} style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px',
                  background: 'var(--bg-secondary)',
                  borderRadius: '8px',
                  marginBottom: '8px',
                  fontSize: '0.85rem'
                }}>
                  <div className={`file-icon ${getFormClass(doc.form_type)}`} style={{ fontSize: '1.1rem' }}>
                    {getFormIcon(doc.form_type)}
                  </div>
                  <div style={{ overflow: 'hidden' }}>
                    <div style={{ fontWeight: 600, fontSize: '0.8rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {getInstitutionName(doc) || doc.form_type}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {doc.form_type} • {doc.filename}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', fontStyle: 'italic' }}>
              No documents uploaded (Manual Entry)
            </div>
          )}
          <div style={{ marginTop: '16px', paddingTop: '12px', borderTop: '1px solid var(--border-color)' }}>
            <button className="btn btn-secondary btn-sm" style={{ width: '100%', fontSize: '0.85rem' }} onClick={onBack}>
              ← Edit Income
            </button>
          </div>
        </div>
      </div>

      {/* CENTER COLUMN - Tax Report */}
      <div>

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
              <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Federal</span>
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
              <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>{getStateName(state)}</span>
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
            <div style={{ marginTop: 'var(--space-sm)', fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
              {results.total_wages > 0 && <div>Wages: {formatCurrency(results.total_wages)}</div>}
              {results.total_interest > 0 && <div>Interest: {formatCurrency(results.total_interest)}</div>}
              {results.total_dividends > 0 && (
                <div>
                  Dividends: {formatCurrency(results.total_dividends)}
                  {results.federal?.qualified_dividends > 0 && (
                    <span style={{ opacity: 0.7 }}> (Qualified: {formatCurrency(results.federal.qualified_dividends)})</span>
                  )}
                </div>
              )}
              {results.total_capital_gains !== 0 && <div>Capital Gains: {formatCurrency(results.total_capital_gains)}</div>}
              {results.total_self_employment > 0 && <div>Self-Employment: {formatCurrency(results.total_self_employment)}</div>}
            </div>
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
            <div className="card-icon">F</div>
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
              {results.federal.additional_medicare_tax > 0 && (
                <tr>
                  <td>Additional Medicare Tax</td>
                  <td style={{ textAlign: 'right' }}>{formatCurrency(results.federal.additional_medicare_tax)}</td>
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

        {/* State Tax Breakdown */}
        <div className="card" style={{ marginBottom: 'var(--space-lg)' }}>
          <div className="card-header">
            <div className="card-icon">{getStateIcon(state)}</div>
            <div>
              <h2 className="card-title">{getStateName(state)} Tax Breakdown</h2>
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
      </div>

      {/* RIGHT COLUMN - Action Buttons */}
      <div className="no-print" style={{ position: 'sticky', top: '90px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
        <button className="side-panel-btn primary" onClick={onViewForms}>
          <span className="btn-icon" style={{ fontSize: '1rem', fontWeight: 700 }}>PDF</span>
          <span className="btn-text">
            <span className="btn-label">Generate Forms</span>
            <span className="btn-desc">Download 1040 PDF</span>
          </span>
        </button>

        <button className="side-panel-btn primary" onClick={onViewLaws}>
          <span className="btn-icon" style={{ fontSize: '1rem', fontWeight: 700 }}>IRC</span>
          <span className="btn-text">
            <span className="btn-label">Tax Law Breakdown</span>
            <span className="btn-desc">See which laws apply</span>
          </span>
        </button>

        <div className="side-panel-divider" />

        <button className="side-panel-btn" onClick={onBack}>

          <span className="btn-text">
            <span className="btn-label">Edit Income</span>
          </span>
        </button>

        <button className="side-panel-btn" onClick={onStartOver}>

          <span className="btn-text">
            <span className="btn-label">Start Over</span>
          </span>
        </button>
      </div>

    </div>
  );
}

// Tax Law Breakdown Component
function TaxLawBreakdown({ results, state, onBack }) {
  if (!results) return null;

  const fed = results.federal;
  const cal = results.california;

  // Build the list of laws with their dollar impact
  const buildLawEntries = () => {
    const entries = [];

    // Federal deduction
    if (fed.standard_deduction > 0) {
      // Estimate tax savings from standard deduction using marginal rate
      const deductionSavings = fed.standard_deduction * (fed.marginal_rate / 100);
      entries.push({
        name: 'Standard Deduction',
        cite: 'IRC §63 — Tax Cuts and Jobs Act of 2017',
        desc: `$${fed.standard_deduction.toLocaleString()} deduction reduces taxable income`,
        amount: -deductionSavings,
        type: 'deduction',
        icon: '—',
        section: 'Federal Deductions',
      });
    }

    // Federal bracket taxes
    if (fed.bracket_breakdown?.length > 0) {
      fed.bracket_breakdown.forEach((bracket) => {
        const rate = (bracket.rate * 100).toFixed(0);
        entries.push({
          name: `${rate}% Income Tax Bracket`,
          cite: 'IRC §1(j)(2)(A) — Federal Income Tax',
          desc: `${formatCurrency(bracket.income_in_bracket)} taxed at ${rate}%`,
          amount: bracket.tax_in_bracket,
          type: 'tax',
          icon: '§',
          section: 'Federal Income Tax',
        });
      });
    }

    // Capital gains tax
    if (fed.capital_gains_tax > 0) {
      entries.push({
        name: 'Preferential Capital Gains Rate',
        cite: 'IRC §1(h) — Long-term capital gains & qualified dividends',
        desc: 'Lower rate for long-term gains and qualified dividends',
        amount: fed.capital_gains_tax,
        type: 'tax',
        icon: '§',
        section: 'Federal Income Tax',
      });
    }

    // Self-employment tax
    if (fed.self_employment_tax > 0) {
      entries.push({
        name: 'Self-Employment Tax (SECA)',
        cite: 'IRC §1401 — Social Security & Medicare',
        desc: '15.3% on net self-employment income (12.4% SS + 2.9% Medicare)',
        amount: fed.self_employment_tax,
        type: 'tax',
        icon: '§',
        section: 'Federal Payroll & Other Taxes',
      });
    }

    // Additional Medicare Tax
    if (fed.additional_medicare_tax > 0) {
      entries.push({
        name: 'Additional Medicare Tax',
        cite: 'IRC §3101(b)(2) — Affordable Care Act (2010)',
        desc: '0.9% on earnings over $200,000 (single)',
        amount: fed.additional_medicare_tax,
        type: 'tax',
        icon: '§',
        section: 'Federal Payroll & Other Taxes',
      });
    }

    // California state tax
    if (cal.state_tax > 0) {
      entries.push({
        name: 'California Income Tax',
        cite: 'CA Rev. & Tax. Code §17041',
        desc: `Progressive rates from 1% to 12.3% on CA taxable income`,
        amount: cal.state_tax,
        type: 'tax',
        icon: '§',
        section: `${getStateName(state)} Taxes`,
      });
    }

    // California mental health surcharge
    if (cal.mental_health_surcharge > 0) {
      entries.push({
        name: 'Mental Health Services Tax',
        cite: 'Proposition 63 (2004) — Mental Health Services Act',
        desc: '1% surcharge on income over $1,000,000',
        amount: cal.mental_health_surcharge,
        type: 'tax',
        icon: '§',
        section: `${getStateName(state)} Taxes`,
      });
    }

    // California deduction
    if (cal.standard_deduction > 0) {
      const stateDeductionSavings = cal.standard_deduction * (cal.marginal_rate / 100);
      entries.push({
        name: 'CA Standard Deduction',
        cite: 'CA Rev. & Tax. Code §17073.5',
        desc: `$${cal.standard_deduction.toLocaleString()} CA deduction`,
        amount: -stateDeductionSavings,
        type: 'deduction',
        icon: '—',
        section: `${getStateName(state)} Deductions`,
      });
    }

    return entries;
  };

  const entries = buildLawEntries();
  const totalTax = results.total_tax_liability;

  // Group by section, preserving order
  const sections = [];
  const sectionMap = {};
  entries.forEach((entry) => {
    if (!sectionMap[entry.section]) {
      sectionMap[entry.section] = [];
      sections.push(entry.section);
    }
    sectionMap[entry.section].push(entry);
  });

  // Sort within each section by absolute amount (largest first)
  sections.forEach((s) => {
    sectionMap[s].sort((a, b) => Math.abs(b.amount) - Math.abs(a.amount));
  });

  return (
    <div className="fade-in">
      <div className="no-print" style={{ marginBottom: '20px' }}>
        <button className="btn btn-secondary" onClick={onBack}>← Back to Results</button>
      </div>

      <div className="law-breakdown">
        <div className="law-breakdown-header">
          <h2>Tax Law Breakdown</h2>
          <p>Every dollar of your tax bill, traced to the law that created it</p>
        </div>

        <div className="law-breakdown-total">
          <div className="total-label">Total Tax Liability</div>
          <div className="total-amount">{formatCurrency(totalTax)}</div>
          <p className="summary-note">
            Federal: {formatCurrency(fed.total_federal_tax)} + {getStateName(state)}: {formatCurrency(cal.total_california_tax)}
          </p>
        </div>

        {sections.map((section) => (
          <div key={section} className="law-section">
            <div className="law-section-title">{section}</div>
            {sectionMap[section].map((entry, i) => (
              <div key={i} className="law-card">
                <div className={`law-card-icon ${entry.type}`}>
                  {entry.icon}
                </div>
                <div className="law-card-body">
                  <div className="law-card-name">{entry.name}</div>
                  <div className="law-card-cite">{entry.cite}</div>
                  <div className="law-card-desc">{entry.desc}</div>
                </div>
                <div className={`law-card-amount ${entry.type}`}>
                  {entry.amount < 0 ? '-' : '+'}{formatCurrency(Math.abs(entry.amount))}
                </div>
              </div>
            ))}
          </div>
        ))}
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
    estimated_tax_payments: 0,
    other_withholding: 0,
    filing_status: 'single',
    state: 'CA',
  });
  const [results, setResults] = useState(null);
  const [isCalculating, setIsCalculating] = useState(false);

  const handleCalculate = async () => {
    setIsCalculating(true);
    try {
      // Sanitize inputs: Convert empty strings to 0 and ensure numbers
      const sanitizedData = Object.fromEntries(
        Object.entries(formData).map(([key, val]) => [
          key,
          (val === '' || val === null || val === undefined) ? 0 : Number(val)
        ])
      );

      const response = await fetch(`${API_BASE}/api/calculate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(sanitizedData),
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
      estimated_tax_payments: 0,
      other_withholding: 0,
      filing_status: 'single',
      state: 'CA',
    });
    setResults(null);
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <div className="app-logo">
            <div>
              <h1 className="app-title">OpenTax</h1>
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
            state={formData.state || 'CA'}
            uploadedDocs={uploadedDocs}
            onBack={() => setStep(2)}
            onStartOver={handleStartOver}
            onViewForms={() => setStep(4)}
            onViewLaws={() => setStep(5)}
          />
        )}

        {step === 4 && (
          <div className="fade-in">
            <div className="no-print" style={{ marginBottom: '20px', padding: '0 20px' }}>
              <button className="btn btn-secondary" onClick={() => setStep(3)}>← Back to Results</button>
            </div>
            <TaxForms results={results} formData={formData} />
          </div>
        )}

        {step === 5 && (
          <TaxLawBreakdown
            results={results}
            state={formData.state || 'CA'}
            onBack={() => setStep(3)}
          />
        )}
      </main>

      <footer style={{
        textAlign: 'center',
        padding: 'var(--space-lg) var(--space-md)',
        color: 'var(--text-muted)',
        fontSize: '0.75rem',
        lineHeight: 1.6,
        borderTop: '1px solid var(--border-color)',
        marginTop: 'var(--space-xl)',
      }}>
        <p style={{ marginBottom: '4px' }}>
          <strong>OpenTax is currently in beta.</strong> Calculations may contain errors.
        </p>
        <p>
          This tool is for informational purposes only and does not constitute tax advice.
          Always consult a qualified tax professional before filing.
        </p>
        <p style={{ marginTop: '4px' }}>
          Document uploads are processed locally in your browser/server to extract data.
          No data is sent to external AI services. All calculations run locally.
        </p>
      </footer>
    </div>
  );
}

export default App;
