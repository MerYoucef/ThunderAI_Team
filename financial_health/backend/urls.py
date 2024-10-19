from django.urls import path
from .views import *
from .api import *



urlpatterns=[
    path('login/', Login.as_view(), name='loginup'),
    path('logout/', Logout.as_view(), name='logout'),
    path('signup/',Signup.as_view(), name='signup'),
    # Retrieve data of dashboard
    path('financial-data/', FinancialDataListCreateView.as_view(), name='financial-data-list'),
    # Customise the generation report 
    path('filtered-financial-data/', FilteredFinancialDataAPIView.as_view(), name='filtered_financial_data'),
    # generate PDF report
    path('financial-data/plot/', FinancialDataPlotAPIView.as_view(), name='financial-data-plot'), # generate the pngs
    # generate CSV file
    path('export-financial-data-csv/', ExportFinancialDataCSV.as_view(), name='financial_data_export_CSV'),
    # generate EXcel file
    path('export-financial-data-excel/', ExportFinancialDataEXCEL.as_view(), name='export_financial_data_excel'),
    # plot For categorical data (not customizeit yet)
    path('cash-flow-plot/', CashFlowPlotAPIView.as_view(), name='cash-flow-plot'),
    path('revenue-expenses-plot/', RevenueExpensesPlotAPIView.as_view(), name='revenue-expenses-plot'),


]