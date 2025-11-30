import os
from dotenv import load_dotenv
import google.generativeai as genai
import pandas as pd
import re
import speech_recognition as sr
import pyttsx3

# ----------------------------
# Setup Gemini AI
# ----------------------------
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("models/gemini-2.5-flash")

# ----------------------------
# Load Employee Data
# ----------------------------
CSV_FILE = "employee_data.csv"
df = pd.read_csv(CSV_FILE)

# ----------------------------
# Text to Speech (Windows Driver)
# ----------------------------
engine = pyttsx3.init(driverName='sapi5')
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)  # 0 = male, 1 = female
engine.setProperty('rate', 170)

def speak(text):
    print("HR Assistant:", text)
    engine.say(text)
    engine.runAndWait()

# ----------------------------
# Microphone Speech Listener
# ----------------------------
def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Listening...")
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            print("You said:", text)
            return text
        except:
            speak("Sorry, I did not understand.")
            return None

# ----------------------------
# Helper Functions
# ----------------------------
def get_employee(employee_id):
    emp = df[df["employee_id"] == employee_id]
    if emp.empty:
        return None
    return emp.iloc[0]

def save_data():
    df.to_csv(CSV_FILE, index=False)

def get_leave_types(emp):
    return [col.replace("_total","") for col in df.columns if col.endswith("_total")]

def calculate_leave_balance(emp, leave_type):
    remaining = emp[f"{leave_type}_total"] - emp[f"{leave_type}_used"]
    return f"{emp['name']} has {remaining} days remaining in {leave_type.replace('_',' ')}."

def calculate_attendance(emp):
    percent = (emp["days_present"] / emp["total_working_days"]) * 100
    return f"{emp['name']}'s attendance is {percent:.2f}%."

def apply_leave(emp, leave_type, days):
    total = emp[f"{leave_type}_total"]
    used = emp[f"{leave_type}_used"]
    remaining = total - used

    if days > remaining:
        return f"❌ You only have {remaining} days left for {leave_type.replace('_',' ')}."

    df.loc[df["employee_id"] == emp["employee_id"], f"{leave_type}_used"] += days
    save_data()
    return f"✅ {days} days {leave_type.replace('_',' ')} leave applied successfully."

def parse_multiple_leave_requests(q, leave_types):
    req = []
    for lt in leave_types:
        found = re.findall(rf"(\d+).*{lt.replace('_',' ')}", q.lower())
        for x in found:
            req.append((lt, int(x)))
    return req

# ----------------------------
# MAIN HR FUNCTION
# ----------------------------
def ask_hr(emp_id, question):
    emp = get_employee(emp_id)
    if emp is None:
        return "Employee not found."

    leave_types = get_leave_types(emp)
    q = question.lower()

    if "leave balance" in q:
        for lt in leave_types:
            if lt.replace("_"," ") in q:
                return calculate_leave_balance(emp, lt)
        return f"Please specify leave type: {leave_types}"

    if "attendance" in q:
        return calculate_attendance(emp)

    if "apply" in q and "leave" in q:
        req = parse_multiple_leave_requests(question, leave_types)
        if not req:
            return f"Specify leave type and days. Available: {leave_types}"
        res = []
        for lt, days in req:
            res.append(apply_leave(emp, lt, days))
        return "\n".join(res)

    # AI HR fallback responses
    prompt = f"""
    You are an HR Assistant.
    Answer only HR-related queries like leave, attendance, payroll, benefits, policy.
    If not HR question, reply: 'I can only help with HR related questions.'

    Question: {question}
    Employee Name: {emp['name']}
    """
    response = model.generate_content(prompt)
    return response.text.strip()

# ----------------------------
# MAIN APPLICATION LOOP
# ----------------------------
if __name__ == "__main__":
    speak("Welcome to Smart HR Assistant.")

    mode = input("Choose interaction mode (voice/text): ").lower()
    if mode not in ["voice", "text"]:
        speak("Invalid mode selected. Switching to text mode.")
        mode = "text"

    while True:
        try:
            emp_id = int(input("Enter your Employee ID (0 to exit): "))
        except ValueError:
            speak("Please enter a valid number.")
            continue

        if emp_id == 0:
            speak("Thank you. Goodbye!")
            break

        emp = get_employee(emp_id)
        if emp is None:
            speak("Employee ID not found. Try again.")
            continue

        speak(f"Hello {emp['name']}. You may now ask HR questions. Say exit to stop.")

        while True:
            if mode == "voice":
                speak("I am listening...")
                question = listen()
                if question is None:
                    continue
            else:
                question = input("Ask your HR question: ")

            if question.lower() in ["exit", "quit", "stop"]:
                speak("Ending conversation. Goodbye!")
                break

            answer = ask_hr(emp_id, question)
            speak(answer)
            print("\nHR Assistant:", answer)
