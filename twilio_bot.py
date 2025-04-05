
from fastapi import FastAPI, Request, Form
from fastapi.responses import PlainTextResponse
from twilio.rest import Client
from dotenv import load_dotenv
import os
import re
# Load environment
load_dotenv()

TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP = "whatsapp:+14155238886"

client = Client(TWILIO_SID, TWILIO_TOKEN)

app = FastAPI()


from app.gemini_service import generate_gemini_fact_check
from app.serper_service import fetch_serper_fact_check
@app.post("/whatsapp")
async def whatsapp_webhook(
    request: Request,
    Body: str = Form(...),
    From: str = Form(...)
):
    try:
        print(f"📩 Message from {From}: {Body}")

        # Fact-check logic
        serper_data = await fetch_serper_fact_check(Body)
        gemini_result = await generate_gemini_fact_check(Body, serper_data)

       

        source_links = "\n".join(
        [f"🔗 {src['link']}" for src in gemini_result.sources[:3]]  # limit to top 3
        ) if gemini_result.sources else "No sources found."

        # Clean explanation 
        explanation_clean = gemini_result.explanation

        # Remove markdown-style bold/italics + section headers
        explanation_clean = re.sub(r"\{1,2}(.?)\*{1,2}", r"\1", explanation_clean)  # Remove * and **

        # Remove the "Verified Sources" section from explanation completely
        explanation_clean = re.sub(r"(?i)(Verified Sources:).*", "", explanation_clean, flags=re.DOTALL)

        # Also clean typical headings
        for label in ["Statement:", "Truth Value:", "Confidence Score:", "Explanation:"]:
            explanation_clean = explanation_clean.replace(label, "")

        # Strip any extra whitespace
        explanation_clean = explanation_clean.strip()

        response_msg = f"""

{explanation_clean}

🌐 Verified Sources:
{source_links}
"""

        # Send reply back
        client.messages.create(
            body=response_msg,
            from_=TWILIO_WHATSAPP,
            to=From
        )

        

    except Exception as e:
        print("❌ Error:", str(e))
        return PlainTextResponse("Something went wrong", status_code=500)