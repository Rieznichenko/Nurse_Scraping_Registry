import datetime
import re
from decimal import Decimal
from typing import Optional, Tuple


def extract_digits(input_string):
    digits = re.findall(r"\d", input_string)
    result = "".join(digits)

    return result


def convert_k_to_float(input_string: str) -> float:
    input_string = input_string.strip().lower()
    input_string = input_string.replace(",", "")
    if input_string.endswith("k"):
        return float(Decimal(input_string.replace("k", "")) * 1000)
    else:
        return float(input_string)


def extract_currency_and_amount(input_string) -> Optional[Tuple[str, float]]:
    pattern = re.compile(r"([A-Za-z€£$]+)\s*([0-9,.]+)")
    match = pattern.match(input_string)

    if match:
        currency = match.group(1)
        amount = float(match.group(2).replace(",", ""))
        return currency, amount
    else:
        return None


def parse_date(input_date_string: str, input_date_format: str, output_date_format: str = "%Y-%m-%d") -> str:
    try:
        return datetime.datetime.strptime(input_date_string, input_date_format).strftime(output_date_format)
    except ValueError:
        pass


def parse_time(input_time_string: str, input_time_format: str, output_time_format: str = "%H:%M") -> Optional[str]:
    try:
        return datetime.datetime.strptime(input_time_string, input_time_format).strftime(output_time_format)
    except ValueError:
        pass


if __name__ == "__main__":
    print(extract_currency_and_amount("+$6"))
