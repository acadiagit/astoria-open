# [utils/gemini_model_test.py]
# Purpose: A definitive test using the correct Vertex AI library
#          to confirm Google Cloud authentication and API access.

import os
from dotenv import load_dotenv
# Import the correct library
from langchain_google_vertexai import ChatVertexAI

print("--- Loading environment variables... ---")
load_dotenv()

GOOGLE_PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
if not GOOGLE_PROJECT_ID:
    print("🛑 FAILED: GOOGLE_CLOUD_PROJECT environment variable not set.")
    exit()

print(f"--- Initializing ChatVertexAI for project: {GOOGLE_PROJECT_ID} ---")
try:
    # This class automatically finds your gcloud ADC credentials.
    # It does not need an API key if you are authenticated via gcloud CLI.
    llm = ChatVertexAI(
        model_name="gemini-1.5-flash-001", # CORRECTED: Using a standard, available model
        project=GOOGLE_PROJECT_ID,
        location="us-central1"
    )
    print("--- Model initialized successfully. ---")

    print("--- Invoking model... ---")
    response = llm.invoke("Give me a one-sentence description of SQL.")

    print("\n--- ✅ SUCCESS! ---")
    print("Model Response:")
    print(response.content)
    print("------------------\n")

except Exception as e:
    print("\n--- 🛑 FAILED ---")
    print(f"An error occurred: {e}")
    print("Check your Google Cloud project ID and Vertex AI permissions.")
    print("----------------\n")

[#--end-of-file--]
