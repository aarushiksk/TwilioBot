from fastapi import FastAPI, HTTPException, Form
import json
import google.generativeai as genai
import os
from dotenv import load_dotenv
import re
from pydantic import BaseModel

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')


class FactCheckResponse(BaseModel):
    query: str
    is_fact: bool
    confidence_score: float 
    category: str
    explanation: str
    sources: list

async def generate_gemini_fact_check(text: str, serper_data: dict):
    """Use Gemini to process fact-checking with Serper's context"""
    try:
        context_info = json.dumps(serper_data, indent=2)

        prompt = f"""
        Fact-Check this statement: "{text}"

        Here are the search results from a trusted fact-checking API:
        {context_info}

        Based on this, determine:
        - Whether the statement is true or false.
        - Explain why this is fact or misinformation.

        Keep the response structured, short and concise.

        At the end of your response, add this:
        *Category:* Classify the topic into a one-word category (e.g., Politics, Health, History, Tech, Economy).
        """

        response = model.generate_content(prompt)
        response.resolve()

        # Parse LLM output
        output_text = response.text

        is_fact = "false" not in output_text.lower()
        confidence_match = re.search(r"\\*Confidence Score:\\\s([0-1](?:\.\d+)?)", output_text)
        confidence_score = float(confidence_match.group(1)) if confidence_match else 0.5 # Rough heuristic
        category_match = re.search(r"\\*Category:\\\s(\w+)", output_text)
        category = category_match.group(1) if category_match else "Unknown"
        print("Confidence Score:", confidence_score)
        return FactCheckResponse(
            query=text,
            is_fact=is_fact,
            confidence_score=confidence_score,
            category=category,
            explanation=output_text,
            sources=serper_data.get("organic", [])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing fact check: {str(e)}")