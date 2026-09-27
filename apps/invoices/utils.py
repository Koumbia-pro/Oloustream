_UNITS = ["zéro", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf",
          "dix", "onze", "douze", "treize", "quatorze", "quinze", "seize",
          "dix-sept", "dix-huit", "dix-neuf"]
_TENS = {2: "vingt", 3: "trente", 4: "quarante", 5: "cinquante", 6: "soixante"}


def _below_100(n):
    if n < 20:
        return _UNITS[n]
    ten, unit = divmod(n, 10)
    if ten in (7, 9):  # 70-79 = soixante-dix…, 90-99 = quatre-vingt-dix…
        base = "soixante" if ten == 7 else "quatre-vingt"
        if ten == 7 and unit == 1:
            return "soixante et onze"
        return f"{base}-{_UNITS[10 + unit]}"
    if ten == 8:
        return "quatre-vingts" if unit == 0 else f"quatre-vingt-{_UNITS[unit]}"
    word = _TENS[ten]
    if unit == 0:
        return word
    if unit == 1:
        return f"{word} et un"
    return f"{word}-{_UNITS[unit]}"


def _below_1000(n, final=True):
    hundred, rest = divmod(n, 100)
    parts = []
    if hundred:
        if hundred == 1:
            parts.append("cent")
        else:
            # « cents » prend un s seulement s'il termine le nombre
            parts.append(f"{_UNITS[hundred]} cent" + ("s" if rest == 0 and final else ""))
    if rest:
        word = _below_100(rest)
        if not final and word == "quatre-vingts":
            word = "quatre-vingt"
        parts.append(word)
    return " ".join(parts)


def number_to_words_french(n):
    """Convertit un entier positif en lettres, selon l'orthographe française traditionnelle."""
    n = int(n)
    if n == 0:
        return "zéro"
    if n < 0:
        return "moins " + number_to_words_french(-n)

    scales = [(10 ** 9, "milliard"), (10 ** 6, "million")]
    parts = []
    for value, name in scales:
        count, n = divmod(n, value)
        if count:
            parts.append(f"{number_to_words_french(count)} {name}{'s' if count > 1 else ''}")
    thousands, n = divmod(n, 1000)
    if thousands:
        parts.append("mille" if thousands == 1 else f"{_below_1000(thousands, final=False)} mille")
    if n:
        parts.append(_below_1000(n))
    return " ".join(parts)


def generate_qr_code(data):
    """Génère un QR code"""
    import qrcode
    from io import BytesIO
    import base64
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return base64.b64encode(buffer.getvalue()).decode()