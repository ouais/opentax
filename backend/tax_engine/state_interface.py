from abc import ABC, abstractmethod
from typing import Dict, Any, TypedDict, List

class StateTaxResult(TypedDict):
    """Standardized result format for any state tax calculation."""
    total_taxable_income: float
    total_state_tax: float
    standard_deduction: float
    # Optional fields (may be 0 or empty for simple states)
    exemption_credit: float
    bracket_breakdown: List[Any]
    effective_rate: float
    mental_health_tax: float  # CA specific, but can be 0 elsewhere
    # Add other common credits

class StateTaxInput(TypedDict):
    """Standardized input for state tax calculation."""
    wages: float
    interest_income: float
    dividend_income: float
    capital_gains: float
    self_employment_income: float
    tax_year: int
    # Add other needed fields (e.g. federal_agi for states that use it)
    federal_agi: float
    federal_taxable_income: float
    filing_status: str

class StateTaxCalculator(ABC):
    """Abstract base class for state tax implementations."""

    @abstractmethod
    def calculate(self, tax_input: StateTaxInput) -> StateTaxResult:
        """Calculate tax liability for the state."""
        pass
        
    @abstractmethod
    def get_standard_deduction(self, filing_status: str, tax_year: int) -> float:
        """Return standard deduction for the state."""
        pass
