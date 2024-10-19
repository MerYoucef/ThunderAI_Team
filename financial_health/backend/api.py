import google.generativeai as genai
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse

app = FastAPI()

GOOGLE_API_KEY = 'AIzaSyCl1UpKx-JDl09jv20NrzpnR1yJBXE3nco'
genai.configure(api_key=GOOGLE_API_KEY)

model = genai.GenerativeModel("gemini-1.5-flash")

@app.post("/interpret")
async def interpret_graph(file: UploadFile = File(...)):
    file_location = f"/tmp/{file.filename}"
    with open(file_location, "wb+") as file_object:
        file_object.write(await file.read())

    myfile = genai.upload_file(file_location)

    result = model.generate_content([myfile, "\n\n", "Can you interpret this graph?"])

    return JSONResponse(content={"result": result.text})
# from django.http import JsonResponse
# from rest_framework.views import APIView
# from rest_framework.parsers import MultiPartParser
# import google.generativeai as genai

# # Configure the Google API key
# GOOGLE_API_KEY = 'AIzaSyCl1UpKx-JDl09jv20NrzpnR1yJBXE3nco'
# genai.configure(api_key=GOOGLE_API_KEY)

# model = genai.GenerativeModel("gemini-1.5-flash")

# class InterpretGraphAPIView(APIView):
#     parser_classes = [MultiPartParser]  # Allow file uploads

#     def post(self, request):
#         # Check if the file is included in the request
#         if 'file' not in request.data:
#             return JsonResponse({"error": "File is required."}, status=400)

#         # Save the uploaded file temporarily
#         file = request.data['file']
#         file_location = f"/tmp/{file.name}"

#         # Save the file to the specified location
#         with open(file_location, 'wb+') as file_object:
#             for chunk in file.chunks():
#                 file_object.write(chunk)

#         # Use Google Generative AI to interpret the graph
#         myfile = genai.upload_file(file_location)
#         result = model.generate_content([myfile, "\n\n", "Can you interpret this graph?"])

#         # Return the result as a JSON response
#         return JsonResponse({"result": result.text})



