# google_model_test.py
# Purpose: A minimal unit test to confirm the Google Vertex AI library
# can authenticate and make a simple API call.
# This replaces the test for the broken 'genai' library.
# --- CORRECTED: 11/17/2025 ---

import os
import traceback
from dotenv import load_dotenv
from langchain_google_vertexai import ChatVertexAI

print("--- [START] Minimal Google Vertex AI Library Test ---")

# 1. Load environment variables
load_dotenv()
project = os.getenv("GOOGLE_CLOUD_PROJECT")
google_api_key = os.getenv("GOOGLE_API_KEY") # VertexAI uses this implicitly

# 2. Check for necessary credentials
if not project:
    print("!!! [FAIL] GOOGLE_CLOUD_PROJECT not found in .env file.")
    exit(1)
print(f"✅ GOOGLE_CLOUD_PROJECT loaded: {project}")

if not google_api_key:
    print("!!! [FAIL] GOOGLE_API_KEY not found in .env file.")
    exit(1)
print("✅ GOOGLE_API_KEY loaded.")


try:
    # 3. Instantiate the VertexAI LLM
    # This is the step that tests the new library.
    print("Attempting to instantiate ChatVertexAI('gemini-2.0-flash')...")
    llm = ChatVertexAI(
        model="gemini-2.0-flash", # The active model we corroborated
        project=project,
        temperature=0,  # <-- FIX: Added missing comma
        location="us-east1" # The valid region we corroborated
    )
    print("✅ LLM instantiated successfully.")

    # 4. Make the simplest possible call
    # This will fail if authentication is wrong or the API is unreachable.
    print("Attempting simple .invoke('Hello, world!')...")
    response = llm.invoke("Hello, world!")
    
    print("\n--- [SUCCESS] ---")
    print("Test passed. The Vertex AI library is working.")
    print("\n[Response from Gemini]:")
    print(response.content)

except Exception as e:
    print("\n--- [FAIL] ---")
    print("Test failed. The Vertex AI library is broken or misconfigured.")
    print("\n[Full Error]:")
    traceback.print_exc()

print("--- [END] Test Complete ---")
