import qrcode

def number_to_words_french(n):
    """Convertit un nombre en lettres (français)"""
    if n == 0:
        return "zéro"
    
    units = ["", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf"]
    teens = ["dix", "onze", "douze", "treize", "quatorze", "quinze", "seize", 
             "dix-sept", "dix-huit", "dix-neuf"]
    tens = ["", "dix", "vingt", "trente", "quarante", "cinquante", 
            "soixante", "soixante-dix", "quatre-vingt", "quatre-vingt-dix"]
    
    def convert_hundreds(num):
        result = ""
        
        # Centaines
        hundred = num // 100
        if hundred > 1:
            result += units[hundred] + " cent"
            if num % 100 == 0:
                result += "s"
        elif hundred == 1:
            result += "cent"
        
        # Dizaines et unités
        remainder = num % 100
        if remainder >= 20:
            ten = remainder // 10
            unit = remainder % 10
            if result:
                result += " "
            result += tens[ten]
            if unit > 0:
                if ten == 8:
                    result += "-" + units[unit]
                else:
                    result += ("-" if ten else "") + units[unit]
        elif remainder >= 10:
            if result:
                result += " "
            result += teens[remainder - 10]
        elif remainder > 0:
            if result:
                result += " "
            result += units[remainder]
        
        return result
    
    def convert_group(num, scale):
        if num == 0:
            return ""
        result = convert_hundreds(num)
        if scale:
            result += " " + scale
            if num > 1 and scale != "mille":
                result += "s"
        return result
    
    # Groupes de milliers
    if n < 1000:
        return convert_hundreds(n)
    elif n < 1000000:
        thousands = n // 1000
        hundreds = n % 1000
        result = convert_group(thousands, "mille")
        if hundreds:
            result += " " + convert_hundreds(hundreds)
        return result
    elif n < 1000000000:
        millions = n // 1000000
        remainder = n % 1000000
        result = convert_group(millions, "million")
        if remainder >= 1000:
            result += " " + convert_group(remainder // 1000, "mille")
        if remainder % 1000:
            result += " " + convert_hundreds(remainder % 1000)
        return result
    else:
        return "Nombre trop grand"


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