from rest_framework import serializers 
from backend.models import *


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model=CustomUser
        fields=['id','username','password','first_name','last_name','email','organization','role']



class FinancialDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialData
        fields = ['date', 'revenue', 'expenses', 'cash_inflow','cash_outflow','net_cash_flow','profit']
