"""
Integration tests for the OpenTax application.

Tests the full API endpoints with realistic tax data to verify
calculation, PDF generation, and frontend serving all work end-to-end.

Requires the backend server to be running on localhost:8000.
Run with: pytest tests/test_integration.py -v
"""

import io
import zipfile

import pytest
import requests

BASE_URL = "http://localhost:8000"

SAMPLE_TAX_INPUT = {
    "tax_year": 2024,
    "state": "CA",
    "w2_wages": 85000,
    "w2_federal_withheld": 12000,
    "w2_state_withheld": 3500,
    "w2_social_security_wages": 85000,
    "w2_casdi": 0,
    "interest_income": 250,
    "interest_federal_withheld": 0,
    "ordinary_dividends": 500,
    "qualified_dividends": 400,
    "capital_gain_distributions": 0,
    "dividend_federal_withheld": 0,
    "short_term_gains": 0,
    "long_term_gains": 1500,
    "self_employment_income": 0,
    "self_employment_federal_withheld": 0,
    "estimated_tax_payments": 0,
    "other_withholding": 0,
}

SAMPLE_PII = {
    "firstName": "Test",
    "lastName": "User",
    "ssn": "000-00-0000",
    "address": "123 Test St",
    "city": "San Francisco",
    "state": "CA",
    "zip": "94102",
}


@pytest.fixture(scope="module")
def server_available():
    """Check that the server is running before running tests."""
    try:
        response = requests.get(BASE_URL, timeout=5)
        return True
    except requests.ConnectionError:
        pytest.skip("Backend server not running on localhost:8000")


class TestFrontendServing:
    """Verify the frontend is being served correctly."""

    def test_homepage_loads(self, server_available):
        response = requests.get(BASE_URL)
        assert response.status_code == 200
        assert "OpenTax" in response.text

    def test_homepage_has_no_emojis(self, server_available):
        response = requests.get(BASE_URL)
        html = response.text
        # Common emojis that were previously in the app
        banned_emojis = ["🐻", "🗽", "🤠", "📁", "✏️", "📄", "⚖️", "🔄", "📤", "⏳", "📥"]
        for emoji in banned_emojis:
            assert emoji not in html, f"Found banned emoji {emoji} in homepage HTML"

    def test_static_assets_load(self, server_available):
        homepage = requests.get(BASE_URL)
        # Check that JS and CSS assets are referenced
        assert ".js" in homepage.text
        assert ".css" in homepage.text


class TestCalculateEndpoint:
    """Verify the /api/calculate endpoint works correctly."""

    def test_calculate_basic(self, server_available):
        response = requests.post(f"{BASE_URL}/api/calculate", json=SAMPLE_TAX_INPUT)
        assert response.status_code == 200
        result = response.json()

        # Verify top-level structure
        assert "federal" in result
        assert "california" in result
        assert "total_tax_liability" in result
        assert "amount_owed" in result

    def test_calculate_federal_breakdown(self, server_available):
        response = requests.post(f"{BASE_URL}/api/calculate", json=SAMPLE_TAX_INPUT)
        result = response.json()
        fed = result["federal"]

        assert fed["wages"] == 85000
        assert fed["standard_deduction"] > 0
        assert fed["taxable_income"] > 0
        assert fed["total_federal_tax"] > 0
        assert "bracket_breakdown" in fed
        assert len(fed["bracket_breakdown"]) > 0

    def test_calculate_california_breakdown(self, server_available):
        response = requests.post(f"{BASE_URL}/api/calculate", json=SAMPLE_TAX_INPUT)
        result = response.json()
        cal = result["california"]

        assert cal["gross_income"] > 0
        assert cal["standard_deduction"] > 0
        assert cal["taxable_income"] > 0
        assert cal["state_tax"] > 0
        assert cal["total_california_tax"] > 0

    def test_calculate_zero_income(self, server_available):
        zero_input = {**SAMPLE_TAX_INPUT, "w2_wages": 0, "interest_income": 0,
                      "ordinary_dividends": 0, "qualified_dividends": 0,
                      "long_term_gains": 0, "w2_federal_withheld": 0,
                      "w2_state_withheld": 0, "w2_social_security_wages": 0}
        response = requests.post(f"{BASE_URL}/api/calculate", json=zero_input)
        assert response.status_code == 200
        result = response.json()
        assert result["federal"]["total_federal_tax"] == 0

    def test_calculate_high_income(self, server_available):
        high_input = {**SAMPLE_TAX_INPUT, "w2_wages": 500000,
                      "w2_federal_withheld": 100000, "w2_state_withheld": 30000,
                      "w2_social_security_wages": 500000}
        response = requests.post(f"{BASE_URL}/api/calculate", json=high_input)
        assert response.status_code == 200
        result = response.json()
        # High income should trigger additional Medicare tax
        assert result["federal"]["total_federal_tax"] > 50000

    def test_calculate_with_self_employment(self, server_available):
        se_input = {**SAMPLE_TAX_INPUT, "self_employment_income": 50000}
        response = requests.post(f"{BASE_URL}/api/calculate", json=se_input)
        assert response.status_code == 200
        result = response.json()
        assert result["federal"]["self_employment_tax"] > 0


class TestPdfGenerationEndpoint:
    """Verify the /api/generate-pdf endpoint works for all form types."""

    def test_generate_1040_only(self, server_available):
        payload = {**SAMPLE_TAX_INPUT, "pii": SAMPLE_PII}
        response = requests.post(
            f"{BASE_URL}/api/generate-pdf?form_type=1040",
            json=payload,
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert len(response.content) > 1000  # Valid PDF should be > 1KB

    def test_generate_540_only(self, server_available):
        payload = {**SAMPLE_TAX_INPUT, "pii": SAMPLE_PII}
        response = requests.post(
            f"{BASE_URL}/api/generate-pdf?form_type=540",
            json=payload,
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert len(response.content) > 1000

    def test_generate_all_forms_zip(self, server_available):
        payload = {**SAMPLE_TAX_INPUT, "pii": SAMPLE_PII}
        response = requests.post(
            f"{BASE_URL}/api/generate-pdf?form_type=all",
            json=payload,
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"

        # Verify ZIP contains both PDFs
        zf = zipfile.ZipFile(io.BytesIO(response.content))
        filenames = zf.namelist()
        assert "form1040_2025.pdf" in filenames
        assert "ca540_2025.pdf" in filenames
        assert len(filenames) == 2

        # Verify each PDF inside is valid (non-empty)
        for name in filenames:
            assert len(zf.read(name)) > 1000, f"{name} is too small to be a valid PDF"

    def test_generate_default_is_zip(self, server_available):
        payload = {**SAMPLE_TAX_INPUT, "pii": SAMPLE_PII}
        response = requests.post(f"{BASE_URL}/api/generate-pdf", json=payload)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"
