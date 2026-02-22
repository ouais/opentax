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

        if state_code == 'NY':
            from .states.new_york import NewYorkStateCalculator
            return NewYorkStateCalculator()

        # States with NO income tax
        if state_code in [
            'TX',
            'FL',
            'WA',
            'TN',
            'NV',
            'SD',
            'WY',
            'AK',
                'NH']:
            from .states.no_income_tax import NoIncomeTaxState
            return NoIncomeTaxState()

        # For MVP, default to NoTax (or Generic) to prevent crashes
        # Ideally this would be GenericTaxState with flat rate placeholder
        from .states.no_income_tax import NoIncomeTaxState
        return NoIncomeTaxState()
