import streamlit as st
import sounddevice as sd
from scipy.io.wavfile import write
import wave
import os
import json
from vosk import Model, KaldiRecognizer
import pyttsx3
import pythoncom  # required to initialize COM thread on Windows

def speak(text):
    try:
        pythoncom.CoInitialize()  # ✅ Required fix on Windows
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except RuntimeError:
        pass


st.set_page_config(page_title="Free Insurance Chatbot", layout="centered")
st.title("🤖 Voice + Text Insurance Chatbot")

# Load STT model (vosk)
@st.cache_resource
def load_stt_model():
    return Model("models/vosk-model-small-en-us-0.15")

model = load_stt_model()

def record_audio(filename="input.wav", duration=5):
    fs = 16000
    st.info("🎙 Recording... Speak now.")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    write(filename, fs, recording)
    st.success("✅ Recording done!")

def transcribe_audio(filename="input.wav"):
    wf = wave.open(filename, "rb")
    rec = KaldiRecognizer(model, wf.getframerate())
    rec.SetWords(True)
    results = []

    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            results.append(json.loads(rec.Result()))
    results.append(json.loads(rec.FinalResult()))
    return " ".join([res.get("text", "") for res in results]).strip()

def evaluate_insurance(age, income, dependents, assets, cover):
    age = int(age)
    income = float(income)
    dependents = int(dependents)
    assets = float(assets)
    cover = float(cover)

    multiplier = 15 if age < 40 else 10
    ideal = income * multiplier + (dependents * 5e5) - assets
    ratio = cover / ideal

    if ratio >= 1:
        return "✅ Your current insurance is sufficient.", "Keep reviewing every 5 years and ensure inflation adjustment."
    elif 0.7 <= ratio < 1:
        return "⚠️ Almost sufficient. You may increase it.", "Consider topping up your term insurance by 20-30%."
    elif 0.4 <= ratio < 0.7:
        return "🚨 Not adequate. Consider increasing it.", "You should buy an additional term plan immediately."
    else:
        return "❌ Severely insufficient. Take immediate action.", "Act now by getting a large term cover (e.g., 20x income) and reduce liabilities."

# Session and Navigation
if "stage" not in st.session_state:
    st.session_state.stage = "start"

if st.button("🔄 Restart"):
    st.session_state.stage = "start"

if st.session_state.stage == "start":
    st.write("👋 How can I help you today?")
    
    col1, col2, col3 = st.columns(3)
    if col1.button("📊 Calculate Life Insurance"):
        st.session_state.stage = "calc"
    elif col2.button("🏥 Suggest Health Insurance"):
        st.session_state.stage = "health"
    elif col3.button("🛡 Suggest Life Insurance"):
        st.session_state.stage = "life"

elif st.session_state.stage == "calc":
    st.subheader("📊 Life Insurance Evaluation")
    speak("Please provide your age, income, dependents, assets, and cover.")
    st.write("🎤 You can either record voice or enter manually.")

    with st.form("insurance_form"):
        use_voice = st.checkbox("🎙 Use Voice Input")
        if use_voice:
            record_audio()
            text_input = transcribe_audio()
            st.success("Transcription: " + text_input)
            parts = [int(s) for s in text_input.split() if s.isdigit()]
            if len(parts) >= 5:
                age, income, dependents, assets, cover = parts[:5]
            else:
                st.error("Please mention 5 numbers clearly.")
                st.stop()
        else:
            age = st.text_input("Age", "30")
            income = st.text_input("Annual Income (in ₹)", "600000")
            dependents = st.text_input("Dependents", "2")
            assets = st.text_input("Asset Value (in ₹)", "500000")
            cover = st.text_input("Current Insurance Cover (in ₹)", "2000000")

        submit = st.form_submit_button("Submit")
        if submit:
            result, action = evaluate_insurance(age, income, dependents, assets, cover)
            st.success(result)
            st.info(f"📌 Recommendation: {action}")
            speak(result)

elif st.session_state.stage == "health":
    st.subheader("🏥 Health Insurance Suggestions")
    st.markdown("""
    - [Star Health Comprehensive Plan](https://www.starhealth.in)
    - [Niva Bupa Health Recharge](https://www.nivabupa.com)
    - [Care Health Insurance](https://www.careinsurance.com)
    """)
    speak("Here are some good health insurance plans.")

elif st.session_state.stage == "life":
    st.subheader("🛡 Life Insurance Suggestions")
    st.markdown("""
    - [HDFC Click 2 Protect](https://www.hdfclife.com)
    - [Max Life Smart Secure Plus](https://www.maxlifeinsurance.com)
    - [LIC Tech Term Plan](https://licindia.in)
    """)
    speak("These are the best life insurance options.")
