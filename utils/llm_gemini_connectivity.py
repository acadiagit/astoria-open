# Filename: utils/llm_gemini_connectivity.py
# Purpose: Standalone script to test the connection to the Google Gemini API.
# Action: Run from the root directory to validate API key and environment.

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

def test_gemini_connection():
    """
    Initializes the Gemini model and attempts to get a simple response.
    """
    print("--- Starting Gemini API Connectivity Test ---")
    
    # Load environment variables from .env file in the project root
    load_dotenv()
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ Error: GOOGLE_API_KEY not found in environment variables.")
        print("Please ensure it is set in your .env file.")
        return

    print("✅ GOOGLE_API_KEY found.")

    try:
        # Initialize the ChatGoogleGenerativeAI model
        # Using "gemini-pro" as it's a versatile and widely available model.
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", google_api_key=api_key)
        print("✅ Gemini model initialized successfully.")

        # Define a simple, thematic question to test the model
        question = "list the names of 4 vessels type schooner" 
        print(f"\nSending test prompt: '{question}'")

        # Invoke the model to get a response
        response = llm.invoke(question)

        print("\n✅ Success! Response from Gemini:")
        print("-" * 30)
        print(response.content)
        print("-" * 30)

    except Exception as e:
        print(f"\n❌ An error occurred while connecting to the Gemini API: {e}")
        print("   Please check your API key, billing status, and network connection.")

if __name__ == "__main__":
    test_gemini_connection()
#--end-of-script
