from django.db import models
from django.contrib.auth.models import User
from apps.business_partners.models import Partner
from django.core.validators import MinValueValidator
from decimal import Decimal

class InvoiceTemplate(models.Model):
    """Templates de factures personnalisables"""
    TEMPLATE_CHOICES = [
        ('jofe', 'JO\'FE Digital Style'),
        ('orange', 'Orange Burkina Style'),
        ('custom', 'Personnalisé'),
    ]
    
    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_CHOICES)
    logo = models.ImageField(upload_to='invoices/logos/', blank=True)
    company_name = models.CharField(max_length=200)
    company_address = models.TextField()
    company_phone = models.CharField(max_length=50, blank=True)
    company_email = models.EmailField(blank=True)
    company_website = models.URLField(blank=True)
    
    # Informations bancaires
    bank_name = models.CharField(max_length=100, blank=True)
    rib = models.CharField(max_length=50, blank=True, verbose_name="RIB")
    iban = models.CharField(max_length=50, blank=True, verbose_name="IBAN")
    bic = models.CharField(max_length=20, blank=True, verbose_name="BIC/SWIFT")
    
    # Informations légales
    rccm = models.CharField(max_length=50, blank=True, verbose_name="RCCM")
    ifu = models.CharField(max_length=50, blank=True, verbose_name="IFU")
    
    # Personnalisation
    primary_color = models.CharField(max_length=7, default='#000000')
    secondary_color = models.CharField(max_length=7, default='#666666')
    show_qr_code = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Template de facture"
        verbose_name_plural = "Templates de factures"
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"


class Invoice(models.Model):
    """Factures"""
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('sent', 'Envoyée'),
        ('paid', 'Payée'),
        ('cancelled', 'Annulée'),
        ('overdue', 'En retard'),
    ]
    
    # Numérotation automatique
    invoice_number = models.CharField(max_length=100, unique=True, editable=False)
    
    # Relations
    template = models.ForeignKey(InvoiceTemplate, on_delete=models.PROTECT)
    client = models.ForeignKey(Partner, on_delete=models.PROTECT, related_name='invoices')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    # Informations client (snapshot au moment de la facture)
    client_name = models.CharField(max_length=200)
    client_address = models.TextField()
    client_rccm = models.CharField(max_length=50, blank=True)
    client_ifu = models.CharField(max_length=50, blank=True)
    client_phone = models.CharField(max_length=50, blank=True)
    client_email = models.EmailField(blank=True)
    
    # Détails de la facture
    object_description = models.TextField(verbose_name="Objet de la prestation")
    bc_number = models.CharField(max_length=100, blank=True, verbose_name="N° Bon de Commande")
    
    # Dates
    issue_date = models.DateField(verbose_name="Date d'émission")
    due_date = models.DateField(verbose_name="Date d'échéance", blank=True, null=True)
    
    # Montants
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, 
                                   validators=[MinValueValidator(Decimal('0'))])
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Devise
    currency = models.CharField(max_length=10, default='FCFA')
    
    # Statut
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Modalités de paiement
    payment_terms = models.TextField(blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    # PDF généré
    pdf_file = models.FileField(upload_to='invoices/pdfs/', blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Facture"
        verbose_name_plural = "Factures"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.invoice_number} - {self.client_name}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        
        # Copier les infos client si nouveau
        if not self.client_name and self.client:
            self.client_name = self.client.company_name
            self.client_address = self.client.address or ''
            self.client_rccm = self.client.rccm or ''
            self.client_ifu = self.client.ifu or ''
            self.client_phone = self.client.phone or ''
            self.client_email = self.client.email or ''
        
        super().save(*args, **kwargs)
    
    def generate_invoice_number(self):
        """Génère un numéro de facture unique au format: N-0001/MM/YYYY/AT/OB"""
        from datetime import datetime
        from django.db.models import Max
        
        today = datetime.today()
        year = today.year
        month = today.month
        
        # Trouver le dernier numéro du mois
        last_invoice = Invoice.objects.filter(
            invoice_number__contains=f"/{month:02d}/{year}"
        ).aggregate(Max('invoice_number'))
        
        if last_invoice['invoice_number__max']:
            # Extraire le numéro
            last_num = int(last_invoice['invoice_number__max'].split('-')[1].split('/')[0])
            new_num = last_num + 1
        else:
            new_num = 1
        
        return f"N-{new_num:04d}/{month:02d}/{year}/AT/OB"
    
    def calculate_totals(self):
        """Calcule les totaux"""
        self.subtotal = sum(item.total for item in self.items.all())
        self.tax_amount = (self.subtotal * self.tax_rate) / 100
        self.total = self.subtotal + self.tax_amount
        self.save()
    
    def amount_in_words(self):
        """Convertit le montant en lettres (FCFA)"""
        from .utils import number_to_words_french
        return number_to_words_french(int(self.total))


class InvoiceItem(models.Model):
    """Lignes de facture"""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    
    description = models.CharField(max_length=500)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, 
                                   validators=[MinValueValidator(Decimal('0.01'))])
    unit = models.CharField(max_length=50, default='unité')
    unit_price = models.DecimalField(max_digits=15, decimal_places=2,
                                     validators=[MinValueValidator(Decimal('0'))])
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = "Ligne de facture"
        verbose_name_plural = "Lignes de facture"
        ordering = ['order']
    
    def save(self, *args, **kwargs):
        self.total = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        # Recalculer les totaux de la facture
        self.invoice.calculate_totals()
    
    def __str__(self):
        return f"{self.description} - {self.total} {self.invoice.currency}"