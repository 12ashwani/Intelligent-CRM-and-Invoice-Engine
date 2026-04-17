def number_to_words_indian(amount):
    """
    Convert a number to words in Indian numbering system.
    Handles rupees and paise.
    """
    if amount is None or amount == 0:
        return "Zero Only"

    # Split into rupees and paise
    rupees = int(amount)
    paise = round((amount - rupees) * 100)

    # Convert rupees to words
    rupees_words = _number_to_words(rupees)

    result = f"{rupees_words} Rupee{'s' if rupees != 1 else ''}"

    if paise > 0:
        paise_words = _number_to_words(paise)
        result += f" and {paise_words} Paise"

    result += " Only"
    return result


def _number_to_words(num):
    """Convert number to words using Indian numbering system."""
    if num == 0:
        return "Zero"

    # Indian numbering system units
    units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
    teens = ["Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

    def _convert_below_1000(n):
        if n == 0:
            return ""
        result = ""
        if n >= 100:
            result += units[n // 100] + " Hundred "
            n %= 100
        if n >= 20:
            result += tens[n // 10] + " "
            n %= 10
        elif n >= 10:
            result += teens[n - 10] + " "
            n = 0
        if n > 0:
            result += units[n] + " "
        return result.strip()

    result = ""
    if num >= 10000000:  # Crore
        result += _convert_below_1000(num // 10000000) + " Crore "
        num %= 10000000
    if num >= 100000:  # Lakh
        result += _convert_below_1000(num // 100000) + " Lakh "
        num %= 100000
    if num >= 1000:  # Thousand
        result += _convert_below_1000(num // 1000) + " Thousand "
        num %= 1000
    if num > 0:
        result += _convert_below_1000(num)

    return result.strip()