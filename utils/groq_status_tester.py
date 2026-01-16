# Path: astoria_open/utils/groq_status_tester.py
# Filename: groq_status_tester.py
# Purpose: A minimal script to test the availability of the Groq API.

import os
from dotenv import load_dotenv
from groq import Groq

def test_groq_availability():
    """
    Makes a direct, minimal API call to Groq to check for service availability.
    """
    print("--- Testing Groq API availability... ---")
    try:
        load_dotenv()
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            print("🛑 ERROR: GROQ_API_KEY not found in .env file.")
            return

        client = Groq(api_key=api_key)
        
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": "Hello"}],
            model="llama3-8b-8192",
        )

        print("✅ SUCCESS: Groq API is available and responded.")
        print("Response:", chat_completion.choices[0].message.content)

    except Exception as e:
        print(f"🛑 FAILURE: Could not connect to Groq API.")
        print(f"Error details: {e}")

if __name__ == "__main__":
    test_groq_availability()

#end-of-script
