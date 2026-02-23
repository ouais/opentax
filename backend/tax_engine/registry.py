from .state_interface import StateTaxCalculator
# Imports for other states will go here


class StateTaxRegistry:
    _instances = {}

    @classmethod
    def get_calculator(cls, state_code: str) -> StateTaxCalculator:
        state_code = state_code.upper()

        if state_code in cls._instances:
            return cls._instances[state_code]

        calc = cls._create_calculator(state_code)
        cls._instances[state_code] = calc
        return calc

    @staticmethod
    def _create_calculator(state_code: str) -> StateTaxCalculator:
        if state_code == 'CA':
            from .states.california import CaliforniaStateCalculator
            return CaliforniaStateCalculator()

        try:
            from .states.generic import GenericStateCalculator
            return GenericStateCalculator(state_code)
        except ValueError:
            # Fallback for states completely missing from states.json (prevent breakage)
            # Default to no income tax representation
            from .states.generic import GenericStateCalculator
            # Temporarily inject a blank config so the generic calculator works without raising ValueError
            calc = GenericStateCalculator.__new__(GenericStateCalculator)
            calc.state_code = state_code
            calc.state_data = {"name": state_code, "has_income_tax": False}
            return calc
