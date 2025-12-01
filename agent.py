import google.generativeai as genai
import json
import speech_recognition as sr
import pyttsx3
import sys
import io

# =====================================================
# GEMINI API CONFIG
# =====================================================
genai.configure(api_key="YOUR_API_KEY_HERE")   # <-- replace
model = genai.GenerativeModel("gemini-2.0-flash")

# Fix UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# =====================================================
# VOICE ENGINE (Text-to-Speech)
# =====================================================
engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)
engine.setProperty('rate', 160)


def speak(text):
    """Text-to-speech"""
    text = text.encode('utf-8', 'ignore').decode('utf-8')
    print(f"Agent: {text}", flush=True)
    engine.say(text)
    engine.runAndWait()


# =====================================================
# MICROPHONE (Speech-to-Text)
# =====================================================
def listen():
    """Speech-to-text"""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Listening...", flush=True)
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=6)
            user_text = recognizer.recognize_google(audio)
            print(f"You said: {user_text}", flush=True)
            return user_text.lower()
        except:
            speak("Sorry, I couldn't hear you. Please repeat.")
            return None


# =====================================================
# MEMORY
# =====================================================
memory = {
    "notes": {},
    "study_history": [],
    "weak_topics": []
}

# =====================================================
# EDUCATION TOOLS
# =====================================================
def tool_explain(topic):
    prompt = f"Explain {topic} in very simple language with examples."
    return model.generate_content(prompt).text


def tool_create_notes(topic):
    prompt = f"Explain {topic} in simple bullet-point notes."
    result = model.generate_content(prompt).text
    memory["notes"][topic] = result
    return result


def tool_generate_quiz(topic):
    prompt = f"Generate a 5-question MCQ quiz on {topic}. Include answers."
    return model.generate_content(prompt).text


def tool_study_plan(topic):
    prompt = f"Create a simple 3-day study plan to learn {topic}."
    return model.generate_content(prompt).text


def tool_analyze_weakness():
    if not memory["study_history"]:
        return "You have not studied anything yet."
    last_topic = memory["study_history"][-1]["topic"]
    return f"You may need more practice in: {last_topic}"


# Tools dictionary
TOOLS = {
    "explain": tool_explain,
    "notes": tool_create_notes,
    "quiz": tool_generate_quiz,
    "plan": tool_study_plan,
    "weakness": tool_analyze_weakness
}

# =====================================================
# AGENT CONTROLLER
# =====================================================
def agent_controller(user_input):
    prompt = f"""
You are an Education Agent. Select the correct tool.

TOOLS:
- explain  → explanation, meaning, definition
- notes    → notes, bullet notes, summary
- quiz     → quiz, mcq, test
- plan     → study plan, timetable
- weakness → user asks 'what am I weak at?'

RULES:
1. If unclear → choose "explain".
2. Extract the topic.
3. If no topic → use "general".

User said: "{user_input}"

Reply ONLY in JSON:
{{
  "action": "<tool_name>",
  "topic": "<topic>"
}}
"""

    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"}
    ).text

    try:
        return json.loads(response)
    except:
        return {"action": "explain", "topic": user_input}


# =====================================================
# MAIN AGENT FUNCTION
# =====================================================
def education_agent(user_text):
    decision = agent_controller(user_text)
    action = decision["action"]
    topic = decision["topic"]

    if action not in TOOLS:
        action = "explain"

    result = TOOLS[action](topic)

    memory["study_history"].append({"action": action, "topic": topic})

    return f"Action: {action}\nTopic: {topic}\n\n{result}"


# =====================================================
# MAIN LOOP
# =====================================================
speak("Hello! I am your Education Agent. What would you like to learn today?")

while True:
    user_text = listen()

    if user_text is None:
        continue

    if "exit" in user_text or "quit" in user_text:
        speak("Goodbye! Keep learning and stay curious.")
        break

    reply = education_agent(user_text)
    speak(reply)
