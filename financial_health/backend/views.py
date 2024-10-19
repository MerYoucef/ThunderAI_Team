from backend.serializers import *
from rest_framework import generics 
from django.shortcuts import get_object_or_404
from rest_framework.authtoken.models import Token
from rest_framework import status
from rest_framework.response import Response 
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.hashers import make_password  
import matplotlib.pyplot as plt
from io import BytesIO
from django.http import HttpResponse
import pandas as pd  
from fpdf import FPDF  
import plotly.express as px
from pathlib import Path
import requests
from django.http import JsonResponse
from datetime import date
from rest_framework.views import APIView
import plotly.io as pio
import os
from datetime import datetime
from django.utils.dateparse import parse_date
import google.generativeai as genai
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse

class Login(generics.CreateAPIView):
    serializer_class = UserSerializer
    def post(self, request):
        user = get_object_or_404(CustomUser, username=request.data['username'])
        if not user.check_password(request.data['password']):
            return Response({'detail' : "invalide password"}, status=status.HTTP_404_NOT_FOUND)
        token, created = Token.objects.get_or_create(user= user)
        serializer = self.get_serializer(instance = user)
        return Response({"token": token.key, "user": serializer.data})

class Logout(generics.GenericAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            request.user.auth_token.delete()
            return Response({'detail': 'Successfully logged out.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class Signup(generics.CreateAPIView):
    serializer_class = UserSerializer
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = self.perform_create(serializer)
            token = Token.objects.create(user=user)
            return Response({"token": token.key, "user": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def perform_create(self, serializer):
        password = make_password(self.request.data['password'])
        serializer.save(password=password)  
        return serializer.instance
    

class FinancialDataListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = FinancialData.objects.all()
    serializer_class = FinancialDataSerializer


# Reports plots visualisation and generate pdf ===============================================================================
class GenerateReportPDF(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        output_dir = Path("output")  # Define your output directory here
        try:
            self.generate_pdf_report(output_dir)
            return JsonResponse({"message": "PDF report generated successfully!"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
    def generate_pdf_report(self, output_dir):
        
        # Convert output_dir to Path object if it's not already
        output_dir = Path(output_dir)

        # Define the font color as RGB values (dark gray)
        font_color = (64, 64, 64)

        # Find all PNG files in the output folder
        chart_filenames = list(output_dir.glob("*.png"))

        # Create a PDF document and set the page size
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 24)

        # Add the overall page title
        title = f"Financial Report of {date.today().strftime('%d/%m/%Y')}"
        pdf.set_text_color(*font_color)
        pdf.cell(0, 20, title, align='C', ln=1)
        pdf.ln(10)  # Add a space after the title

        # Add each chart to the PDF document
        for chart_filename in chart_filenames:
            pdf.ln(10)  # Add padding at the top of the next chart
            pdf.image(str(chart_filename), x=10, y=None, w=pdf.w - 20)  # Adjust margins

        # Save the PDF document to a file on disk
        pdf_output_path = output_dir / "report.pdf"
        pdf.output(str(pdf_output_path), "F")
        print(f"PDF report saved successfully at {pdf_output_path}")


class FinancialDataPlotAPIView(APIView):
    permission_classes = [IsAuthenticated]  # Require authentication

    def post(self, request):
        # Extract data from the request body
        metrics = request.data.get('metrics')  # e.g., ['revenue', 'expenses']
        start_date = request.data.get('start_date')  # e.g., '2024-01-01'
        end_date = request.data.get('end_date')  # e.g., '2024-01-31'
        title = request.data.get('title', 'Financial Data Over Time')

        api_url = 'http://127.0.0.1:8000/financial-data/'  # URL of your financial data API
        output_dir = 'output'  # Directory to save the plot

        try:
            # Call the function to fetch data and plot it
            self.fetch_and_plot_financial_data(api_url, output_dir, metrics, start_date, end_date, title)

            # Generate PDF report after plotting
            pdf_report = GenerateReportPDF()
            pdf_response = pdf_report.get(request)  # Call the PDF generation method

            return Response({
                "message": "Plot created successfully!",
                "pdf_message": pdf_response.content.decode('utf-8')
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def fetch_and_plot_financial_data(self, api_url, output_dir, metrics, start_date=None, end_date=None, title='Financial Data Over Time'):
        try:
            # Fetch data from Django REST API
            response = requests.get(api_url)
            response.raise_for_status()  # Raise an error for bad responses
            
            # Convert to pandas DataFrame
            data = response.json()
            df = pd.DataFrame(data)
            
            # Convert 'date' to datetime for plotting
            df['date'] = pd.to_datetime(df['date'])
            
            # Filter by date range if provided
            if start_date:
                df = df[df['date'] >= pd.to_datetime(start_date)]
            if end_date:
                df = df[df['date'] <= pd.to_datetime(end_date)]

            # Plot the selected metrics
            if metrics:
                fig = px.line(df, x='date', y=metrics,
                              labels={'value': 'Amount', 'date': 'Date'},
                              title=title,
                              markers=True)

                # Update the legend to make it more readable
                fig.for_each_trace(lambda t: t.update(name=t.name.capitalize()))

                # Save the chart as a PNG image
                output_path = Path(output_dir)
                output_path.mkdir(parents=True, exist_ok=True)  # Create directory if it doesn't exist
                fig.write_image(output_path / f'{title}_report.png', width=1200, height=600, scale=2)  # Save the plot

        except requests.exceptions.RequestException as e:
            raise Exception(f"An error occurred while fetching data: {e}")
        except ValueError as e:
            raise Exception(f"Error processing data: {e}")



# For categorical data
class CashFlowPlotAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        # URL of your financial data API
        api_url = 'http://127.0.0.1:8000/financial-data/'  

        # Fetch financial data
        df = self.fetch_financial_data(api_url)
        
        # Generate and save the bar plot
        plot_image = self.plot_cash_flow(df)

        # Create the HTTP response with the plot image
        return HttpResponse(plot_image, content_type='image/png')

    def fetch_financial_data(self, api_url):
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an error for bad responses
        return pd.DataFrame(response.json())

    def plot_cash_flow(self, df):
        """Generate a bar plot for cash inflow and outflow using Plotly."""
        # Convert 'date' to datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Create a bar plot
        fig = px.bar(df, x='date', y=['cash_inflow', 'cash_outflow'],
                     title='Cash Flow Overview',
                     labels={'value': 'Amount', 'date': 'Date'},
                     color_discrete_sequence=['#76c7c0', '#ff6666'],
                     barmode='stack')

        # Save the plot to a BytesIO object
        buf = BytesIO()
        pio.write_image(fig, buf, format='png')
        buf.seek(0)  # Seek to the beginning of the BytesIO object
        return buf.getvalue()  # Return the image data
    

# generate_csv============================================================
class ExportFinancialDataCSV(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        # Get data from the request body
        start_date = request.data.get('start_date')  # e.g., '2024-01-01'
        end_date = request.data.get('end_date')      # e.g., '2024-01-31'
        metrics = request.data.get('metrics')     # Expecting a list, e.g., ['revenue', 'expenses']

        # Filter the financial data based on start_date and end_date
        financial_data_objs = FinancialData.objects.all()

        if start_date and end_date:
            start_date_parsed = parse_date(start_date)
            end_date_parsed = parse_date(end_date)
            financial_data_objs = financial_data_objs.filter(date__range=(start_date_parsed, end_date_parsed))

        # Serialize the data
        serializer = FinancialDataSerializer(financial_data_objs, many=True)

        # Convert serialized data to a DataFrame
        df = pd.DataFrame(serializer.data)

        # Ensure the date column is included in the output
        if metrics:
            metrics = ['date'] + metrics  # Ensure 'date' is included in the metrics list
            df = df[metrics]  # Filter the DataFrame to include only the specified metrics

        # Generate a unique file name and save the data to a CSV
        file_name = f"output/{'financial_data'}.csv"
        df.to_csv(file_name, encoding="UTF-8", index=False)

        # Return the file path in the response
        return Response({"status": 200, "file": file_name})


    

# generate_excel============================================================
class ExportFinancialDataEXCEL(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        # Get data from the request body
        start_date = request.data.get('start_date')  # e.g., '2024-01-01'
        end_date = request.data.get('end_date')      # e.g., '2024-01-31'
        metrics = request.data.get('metrics')     # Expecting a list, e.g., ['revenue', 'expenses']

        # Filter the financial data based on start_date and end_date
        financial_data_objs = FinancialData.objects.all()

        if start_date and end_date:
            start_date_parsed = parse_date(start_date)
            end_date_parsed = parse_date(end_date)
            financial_data_objs = financial_data_objs.filter(date__range=(start_date_parsed, end_date_parsed))

        # Serialize the data
        serializer = FinancialDataSerializer(financial_data_objs, many=True)

        # Convert serialized data to a DataFrame
        df = pd.DataFrame(serializer.data)

        # Ensure the date column is included in the output
        if metrics:
            metrics = ['date'] + metrics  # Ensure 'date' is included in the metrics list
            df = df[metrics]  # Filter the DataFrame to include only the specified metrics

        # Generate a unique file name and save the data to an Excel file
        file_name = f"output/financial_data.xlsx"
        df.to_excel(file_name, index=False, engine='openpyxl')  # Save as Excel file

        # Return the file path in the response
        return Response({"status": 200, "file": file_name})


# Dashboard ==========================================================
# Customize the generation report =========================================== for the selction of metrics ... return data
class FilteredFinancialDataAPIView(APIView):
    permission_classes = [IsAuthenticated]  # Require authentication
    def post(self, request):
        # Get data from the request body
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        metrics = request.data.get('metrics')  # Expecting a list

        # Check if start_date and end_date are provided
        if not start_date or not end_date:
            return Response({"error": "start_date and end_date are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Filter the financial data based on start_date and end_date
        financial_data_objs = FinancialData.objects.all()
        
        start_date_parsed = parse_date(start_date)
        end_date_parsed = parse_date(end_date)
        financial_data_objs = financial_data_objs.filter(date__range=(start_date_parsed, end_date_parsed))
        serializer = FinancialDataSerializer(financial_data_objs, many=True)
        # Convert serialized data to a list of dictionaries
        data = serializer.data
        # If specific metrics are requested, filter the data
        if metrics:
            filtered_data = []
            for item in data:
                filtered_item = {metric: item[metric] for metric in metrics if metric in item}
                filtered_item['date'] = item['date']  # Ensure date is included
                filtered_data.append(filtered_item)
            data = filtered_data

        # Return the filtered data in the response
        return Response({"status": 200, "data": data}, status=status.HTTP_200_OK)
    



class RevenueExpensesPlotAPIView(APIView):
    def get(self, request):
        api_url = 'http://127.0.0.1:8000/financial-data/'  
        # Fetch financial data
        df = self.fetch_financial_data(api_url)
        # Generate and save the line plot
        plot_image = self.plot_revenue_expenses(df)
        # Create the HTTP response with the plot image
        return HttpResponse(plot_image, content_type='image/png')

    def fetch_financial_data(self, api_url):
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an error for bad responses
        return pd.DataFrame(response.json())

    def plot_revenue_expenses(self, df):
        # Convert 'date' to datetime
        df['date'] = pd.to_datetime(df['date'])

        # Create a line plot
        fig = px.line(df, x='date', y=['revenue', 'expenses'],
                      title='Revenue and Expenses Over Time',
                      labels={'value': 'Amount', 'date': 'Date'},
                      color_discrete_sequence=['#76c7c0', '#ff6666'])

        # Save the plot to a BytesIO object
        buf = BytesIO()
        pio.write_image(fig, buf, format='png')
        buf.seek(0)  # Seek to the beginning of the BytesIO object
        return buf.getvalue()  # Return the image data

class InterpretImageAPIView(APIView):
    """
    APIView to upload an image and request interpretation from the /interpret endpoint.
    """

    def post(self, request):
        # Extract the file from the request
        file = request.FILES.get('file')
        
        if not file:
            return Response({"error": "No file was uploaded."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Save the uploaded file to a temporary directory
            temp_file_path = Path("temp") / file.name
            temp_file_path.parent.mkdir(exist_ok=True)  # Ensure the temp directory exists
            
            with open(temp_file_path, 'wb') as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)

            # Now send the saved file to the /interpret endpoint
            with open(temp_file_path, 'rb') as temp_file:
                files = {'file': temp_file}
                response = requests.post("http://127.0.0.1:8000/interpret", files=files)
                
            # Check if the request to /interpret was successful
            if response.status_code == 200:
                return Response(response.json(), status=status.HTTP_200_OK)
            else:
                return Response({"error": "Failed to interpret the image."}, status=response.status_code)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




