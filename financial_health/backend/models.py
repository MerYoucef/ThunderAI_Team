from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('financialmanager', 'FinancialManager'),
        ('admin', 'Admin'),
    )
    role = models.CharField( max_length=20, choices=ROLE_CHOICES)
    organization = models.CharField( max_length=30,null=True, blank=True)


    def __str__(self):
        return f'{self.username}'
    
    class Meta:
        db_table = 'Users'



# Transaction model
class Transaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    category = models.CharField(max_length=100)  # Optionally link to a Category model
    description = models.TextField(blank=True, null=True)
    transaction_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.transaction_type} - {self.amount}'



# Financial Insight model
class FinancialInsight(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    recommendation = models.TextField()
    performance_indicator = models.DecimalField(max_digits=5, decimal_places=2)
    insight_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Insight for {self.user.username} on {self.insight_date}'


# Financial Report model
class FinancialReport(models.Model):
    REPORT_TYPE_CHOICES = [
        ('cash_flow', 'Cash Flow'),
        ('income_statement', 'Income Statement'),
        ('balance_sheet', 'Balance Sheet'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    report_period = models.CharField(max_length=100)  # E.g., Q1 2024
    report_type = models.CharField(max_length=50, choices=REPORT_TYPE_CHOICES)
    report_content = models.TextField()
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Report for {self.user.username} - {self.report_period}'


# Category model
class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    user_defined = models.BooleanField(default=False)

    def __str__(self):
        return self.name


# Financial Data model
class FinancialData(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # Relating FinancialData to User
    date = models.DateField()
    revenue = models.DecimalField(max_digits=10, decimal_places=2)
    expenses = models.DecimalField(max_digits=10, decimal_places=2)
    profit = models.DecimalField(max_digits=10, decimal_places=2)
    cash_inflow = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cash_outflow = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    net_cash_flow = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"Financial Data for {self.user.username} on {self.date}"

    def save(self, *args, **kwargs):
        # Automatically calculate net cash flow when saving
        if self.cash_inflow and self.cash_outflow:
            self.net_cash_flow = self.cash_inflow - self.cash_outflow
        super(FinancialData, self).save(*args, **kwargs)


