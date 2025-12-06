import os
import io
import requests
from fastapi import FastAPI, UploadFile, HTTPException, File, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from openai import OpenAI
import time
from typing import Optional
from wavespeed import Wavespeed

load_dotenv()

app = FastAPI()
WAVESPEED_API_KEY=os.getenv("WAVESPEED_API_KEY")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # allow all for demo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- D-ID CONFIG ----
DID_API_KEY = os.getenv("DID_API_KEY")
DID_AVATAR_IMAGE_URL = "https://www.dropbox.com/scl/fi/re3bmt2v1m95k6617haeh/avatar1.png?rlkey=au8gm9xlzrz1qwp3shjeupseq&dl=1"  # <-- replace with your avatar image


# -------------------------------
# 1️⃣ SPEECH TO TEXT (OpenAI)
# -------------------------------
def speech_to_text(uploaded_file: UploadFile):
    audio_bytes = uploaded_file.file.read()
    audio_format = "wav"

    if uploaded_file.content_type and "/" in uploaded_file.content_type:
        audio_format = uploaded_file.content_type.split("/")[-1]

    audio_stream = io.BytesIO(audio_bytes)
    audio_stream.name = f"speech.{audio_format}"

    response = client.audio.transcriptions.create(
        model="gpt-4o-transcribe",
        file=audio_stream,
    )

    print(response.text)
    return response.text


# -------------------------------
# 2️⃣ LLM CUSTOMER SERVICE REPLY
# -------------------------------
def generate_reply(user_text):
    response = client.responses.create(
        model="gpt-4o-mini",
        input=[
            {
                "role": "system",
                "content": (
                    "You are a polite, concise AI customer service agent. "
                    "Answer briefly and clearly."
                )
            },
            {
                "role": "user",
                "content": user_text
            }
        ]
    )

    print(response.output_text)
    return response.output_text


# -------------------------------
# 3️⃣ D-ID: CREATE TALK SESSION
# -------------------------------
def did_start_talking(text):
    url = "https://api.d-id.com/talks"
    headers = {
        "Authorization": f"Basic {DID_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "source_url": DID_AVATAR_IMAGE_URL,
        "script": {
            "type": "text",
            "input": text,
            "provider": {"type": "microsoft", "voice_id": "id-ID-GadisNeural"}
        },
        "config": {
            "stitch": True,         
            # "logo": {
            #     "url": "https://www.dropbox.com/scl/fi/gnzrmdxt62u0i5ugufss9/logo.png?rlkey=kvnc59weebce20k3xq56rug4v&dl=1",
            #     "position":[10,-10]
            # }               
            # "driver_expressions": {
            # "expressions": [
            #     {
            #     "expression": "happy"
            #     }
            # ]
            # }
        }
        # "driver_url": "bank://lively/neutral"
    }

    res = requests.post(url, json=payload, headers=headers)
    data = res.json()

    print("D-ID Response:", data)  # 🔥 DEBUG THIS

    if "id" not in data:
        error_kind = data.get("kind")

        if error_kind == "InsufficientCreditsError":
            raise HTTPException(
                status_code=402,
                detail={
                    "message": "D-ID account has insufficient credits to start a talk.",
                    "payload": data
                }
            )
        if error_kind == "UnknownError":
            raise HTTPException(
                status_code=503,
                detail={
                    "message": "D-ID returned an internal error. Please retry in a moment.",
                    "payload": data
                }
            )

        raise HTTPException(
            status_code=502,
            detail={
                "message": "D-ID error while starting talk session.",
                "payload": data
            }
        )

    return data["id"]

# -------------------------------
# 4️⃣ POLL UNTIL VIDEO READY
# -------------------------------
def did_get_video_url(talk_id):
    url = f"https://api.d-id.com/talks/{talk_id}"
    headers = {"Authorization": f"Basic {DID_API_KEY}"}

    while True:
        res = requests.get(url, headers=headers).json()

        # When ready
        if 'error' in res:
            print(res['error'])
            break

        if "result_url" in res:
            return res["result_url"]
        
        print('waiting..')
        time.sleep(0.5)  # wait & retry


# -------------------------------
# 3️⃣ wAVESPEEd: CREATE TALK SESSION
# -------------------------------
def wavespeed_start_talking(text):
    ws = Wavespeed(api_key=WAVESPEED_API_KEY)
    # audio_url = ws.generate_audio(text)
    # print('audio_url',audio_url)

    # if not audio_url:
    #     print('ERROR: no audio!!')
    #     return None
    
    final_url = ws.generate_avatar(
        prompt=f"""She speaks directly to the camera, her lips moving naturally as she says: '{text}'.
        Her gestures are subtle, occasionally raising his hands for emphasis, creating a professional and engaging tone.""",
        model_name='alibaba/wan-2.5/image-to-video',
        additional_payload = {
            # "audio": audio_url,
            "image": DID_AVATAR_IMAGE_URL,
            "enable_prompt_expansion": True,
            "seed": -1,
            "size":"720*1280",
        })
    print('final_url',final_url)
    return final_url

# -------------------------------
# 5️⃣ MAIN ENDPOINT
# -------------------------------
@app.post("/talk")
async def talk(
    audio: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
):
    # 1) Determine user text source
    user_text = None
    if text and text.strip():
        user_text = text.strip()
    elif audio is not None:
        user_text = speech_to_text(audio)
    else:
        raise HTTPException(
            status_code=400,
            detail="No audio or text provided. Please record audio or type a message.",
        )

    # 2) Generate LLM response
    assistant_text = generate_reply(user_text)

    # 3) D-ID talk session
    talk_id = did_start_talking(assistant_text)

    # 4) Poll for final video
    video_url = did_get_video_url(talk_id)

    # 3-4 generate and poll
    # video_url = wavespeed_start_talking(assistant_text)

    return {
        "user_text": user_text,
        "assistant_text": assistant_text,
        "video_url": video_url
    }
