import re

__all__ = ['RomanDigit', 'RomanNumeral', 'is_roman_numeral']


class RomanNumeralError(Exception):
    pass


class RomanDigit:
    romandigits = 'IVXLCDM'
    decimaldigits = [1, 5, 10, 50, 100, 500, 1000]

    def __init__(self, digit):
        self.input_digit = digit
        self.decimal = None
        self.roman = None
        self._discern()
        self._solve()

    def _discern(self):
        if isinstance(self.input_digit, int) and self._validate_decimal_input():
            self.decimal = self.input_digit
            return
        elif isinstance(self.input_digit, str) and self._validate_str_input():
            self.roman = self.input_digit.upper()
        else:
            raise TypeError('Can accept int or str only.')

    def _validate_decimal_input(self):
        if self.input_digit in RomanDigit.decimaldigits:
            return True
        else:
            raise ValueError('Passed value has no equal roman digit.')

    def _validate_str_input(self):
        if len(self.input_digit) != 1:
            raise ValueError('Can accept a single roman digit str only.')
        if self.input_digit.upper() in RomanDigit.romandigits:
            return True
        else:
            raise ValueError(f'{self.input_digit} is not a roman digit.')

    def _solve(self):
        if self.decimal:
            self.roman = RomanDigit.romandigits[RomanDigit.decimaldigits.index(self.decimal)]
        else:
            self.decimal = RomanDigit.decimaldigits[RomanDigit.romandigits.index(self.roman)]

    def __eq__(self, other):
        if not isinstance(other, RomanDigit):
            raise ValueError(f'Can not compare RomanDigit to {other.__class__.__name__}')
        return self.decimal == other.decimal

    def __lt__(self, other):
        if not isinstance(other, RomanDigit):
            raise ValueError(f'Can not compare RomanDigit to {other.__class__.__name__}')
        return self.decimal < other.decimal

    def __repr__(self):
        return f"{self.__class__.__name__} {self.roman} {self.decimal}"

    def __str__(self):
        return self.roman


class RomanNumeral(str):
    _mil_re = re.compile(r'(M{1,4})')
    _cent_re = re.compile(r'(CM)|(C[CD]?((?<=C)C)?)|(DC{0,3})')
    _dec_re = re.compile(r'(XC)|(X[XL]?((?<=X)X)?)|(LX{0,3})')
    _uni_re = re.compile(r'(IX)|(I[IV]?((?<=I)I)?)|(VI{0,3})')
    regexes = _mil_re, _cent_re, _dec_re, _uni_re

    def __init__(self, numeral):
        self.input_numeral = numeral
        self.roman = None
        self.decimal = None
        self._groups = None
        self._discern()
        self._solve()

    def _discern(self):
        if isinstance(self.input_numeral, int) and self._validate_decimal_input():
            self.decimal = self.input_numeral
            return
        elif isinstance(self.input_numeral, str) and self._validate_str_input():
            self.roman = self.input_numeral.upper()
        else:
            raise TypeError(f'Can accept int or str only. Passed: {self.input_numeral.__class__}')

    def _validate_decimal_input(self):
        if self.input_numeral < 1:
            raise RomanNumeralError('Roman numeral can not be less than 1.')
        elif self.input_numeral > 4000:
            raise RomanNumeralError('Roman numeral can not be greater than 4000')
        else:
            return True

    def _validate_str_input(self):
        for letter in self.input_numeral:
            if letter.upper() not in RomanDigit.romandigits:
                raise RomanNumeralError(f'One of the letters is not a roman digit: {letter}')
        return True

    def _solve(self):
        if self.decimal:
            self._solve_roman()
        elif self.roman:
            self._solve_groups()
            self._validate_roman()
            self._solve_decimal()
        else:
            raise RuntimeError('Unknown exception.')

    def _solve_roman(self):
        thousands = self.decimal//1000
        hundrets = (self.decimal % 1000)//100
        tens = (self.decimal % 100)//10
        units = self.decimal % 10
        digits = (thousands, hundrets, tens, units)
        tags = (('M', 'MMM'), 'CDM', 'XLC', 'IVX')
        solvers = ((0,), (0, 0), (0, 0, 0), (0, 1), (1,), (1, 0), (1, 0, 0), (1, 0, 0, 0), (0, 2))
        roman = []
        for ind in (0, 1, 2, 3):
            digit = digits[ind]
            if digit:
                for instruction in solvers[digit-1]:
                    roman.append(tags[ind][instruction])
        self.roman = ''.join(roman)

    def _solve_groups(self):
        roman = self.roman
        groups = []
        for reg in RomanNumeral.regexes:

            extraction = reg.match(roman)
            if extraction:
                group = extraction.group()
                groups.append(group)
                # print (group)
                roman = roman[len(group):]
            else:
                groups.append('')
        self._groups = groups

    def _validate_roman(self):
        solved_roman = ''.join(self._groups)
        if self.roman != solved_roman:
            raise RomanNumeralError('Passed roman digit is invalid.')

    def _solve_decimal(self):
        decimal_value = 0
        for group in self._groups:
            group_value = 0
            if group:
                for digit in [RomanDigit(letter) for letter in group]:
                    if group_value < digit.decimal:
                        group_value = digit.decimal - group_value
                    else:
                        group_value += digit.decimal
            decimal_value += group_value
        self.decimal = decimal_value

    @classmethod
    def validate(cls, number):
        RomanNumeral(number)
        return True

    def __eq__(self, other):
        if isinstance(other, RomanNumeral):
            if self.decimal == other.decimal and self.roman == other.roman:
                return True
            elif self.decimal != other.decimal and self.roman != other.roman:
                return False
            else:
                raise RuntimeError('Unknown exception')
        else:
            raise TypeError(f'Can not compare RomanNumeral to {other.__class__}')

    def __lt__(self, other):
        if isinstance(other, RomanNumeral):
            return self.decimal < other.decimal
        else:
            raise TypeError(f'Can not compare RomanNumeral to {other.__class__}')

    def __add__(self, other):
        if isinstance(other, RomanNumeral):
            return RomanNumeral(self.decimal + other.decimal)
        raise TypeError(f'Can not add RomanNumeral to {other.__class__}')

    def __sub__(self, other):
        if isinstance(other, RomanNumeral):
            return RomanNumeral(self.decimal - other.decimal)
        raise TypeError(f'Can not subtract {other.__class__} from RomanNumeral')

    def __repr__(self):
        return f'RomanNumeral {self.decimal} {self.roman}'


def is_roman_numeral(x):
    if isinstance(x, str):
        try:
            RomanNumeral(x)
            return True
        except ValueError:
            return False

