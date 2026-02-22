import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import TaxForms from './TaxForms';

describe('TaxForms Component', () => {
    const mockResults = {
        total_federal_tax: 1000,
        amount_owed: 500,
        federal: {},
        california: { total_california_tax: 200 },
        tax_year: 2024,
        total_wages: 50000,
        total_federal_withheld: 500,
        total_state_withheld: 100
    };

    const mockFormData = {
        w2_wages: 50000,
    };

    beforeEach(() => {
        // Mock globalThis fetch
        globalThis.fetch = vi.fn(() =>
            Promise.resolve({
                ok: true,
                blob: () => Promise.resolve(new Blob(['mock pdf data'], { type: 'application/pdf' })),
            })
        );

        // Mock URL.createObjectURL since it's not present in JSDOM
        globalThis.URL.createObjectURL = vi.fn(() => 'mock-url');

        // Mock document.createElement logic used for downloads
        const mockLink = {
            click: vi.fn(),
            remove: vi.fn(),
            href: '',
            download: '',
        };
        const originalCreateElement = document.createElement.bind(document);
        vi.spyOn(document, 'createElement').mockImplementation((tagName) => {
            if (tagName === 'a') return mockLink;
            return originalCreateElement(tagName);
        });
        const originalAppendChild = document.body.appendChild.bind(document.body);
        vi.spyOn(document.body, 'appendChild').mockImplementation((node) => {
            if (node === mockLink) return;
            return originalAppendChild(node);
        });
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it('should use API_BASE when downloading forms', async () => {
        render(<TaxForms results={mockResults} formData={mockFormData} />);

        // Find the download all button
        const downloadAllButton = screen.getByRole('button', { name: /Download All Forms \(ZIP\)/i });

        // Click it
        fireEvent.click(downloadAllButton);

        // Verify fetch was called with the correct URL
        await waitFor(() => {
            expect(globalThis.fetch).toHaveBeenCalledTimes(1);

            const fetchUrl = globalThis.fetch.mock.calls[0][0];

            // Should contain API_BASE and the correct endpoint
            expect(fetchUrl).toContain('http://localhost:8000/api/generate-pdf');
            expect(fetchUrl).toContain('form_type=all');
        });
    });
});
