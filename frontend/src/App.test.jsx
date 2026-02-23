import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import React from 'react';

import { TaxResults, TaxLawBreakdown } from './App';

describe('NIIT Frontend Rendering Logic', () => {

    const mockNonNIITResults = {
        amount_owed: 100,
        total_federal_withheld: 0,
        total_state_withheld: 0,
        federal: {
            total_federal_tax: 100,
            net_investment_income_tax: 0.0,
            effective_rate: 10,
            marginal_rate: 22,
        },
        california: {
            total_california_tax: 0,
            effective_rate: 0,
            marginal_rate: 0
        }
    };

    const mockNIITResults = {
        amount_owed: 2000,
        total_federal_withheld: 0,
        total_state_withheld: 0,
        federal: {
            total_federal_tax: 2000,
            net_investment_income_tax: 1900.0, // NIIT > 0
            effective_rate: 15,
            marginal_rate: 35,
        },
        california: {
            total_california_tax: 0,
            effective_rate: 0,
            marginal_rate: 0
        }
    };

    it('should not display NIIT when net_investment_income_tax is 0 (TaxResults)', () => {
        const { queryByText } = render(
            <TaxResults
                results={mockNonNIITResults}
                state={'CA'}
                uploadedDocs={[]} />
        );
        expect(queryByText('Net Investment Income Tax (NIIT)')).toBeNull();
    });

    it('should display NIIT in TaxResults when net_investment_income_tax is > 0', () => {
        const { getByText } = render(
            <TaxResults
                results={mockNIITResults}
                state={'CA'}
                uploadedDocs={[]} />
        );
        expect(getByText('Net Investment Income Tax (NIIT)')).toBeDefined();
        // Validate value $1,900.00
        expect(getByText('$1,900.00')).toBeDefined();
    });

    it('should display NIIT in TaxLawBreakdown when net_investment_income_tax is > 0', () => {
        const { getByText } = render(
            <TaxLawBreakdown
                results={mockNIITResults}
                state={'CA'} />
        );
        expect(getByText('Net Investment Income Tax (NIIT)')).toBeDefined();
        expect(getByText('IRC §1411 — Form 8960')).toBeDefined(); // Verify Law citation
    });
});
