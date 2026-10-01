"""Gemini integration with a safe local fallback when no API key is configured."""
from app.config import GOOGLE_API_KEY, WORKOUT_MODEL, TIP_MODEL

def _generate(prompt: str, model_name: str) -> str:
    if not GOOGLE_API_KEY:
        raise RuntimeError("GOOGLE_API_KEY is not configured")
    from google import genai
    client = genai.Client(api_key=GOOGLE_API_KEY)
    response = client.models.generate_content(model=model_name, contents=prompt)
    text = getattr(response, "text", None)
    if not text or not text.strip():
        raise RuntimeError("Gemini returned an empty response")
    return text.strip()

def generate_workout(username: str, age: int, weight: float, goal: str, intensity: str) -> tuple[str, bool]:
    prompt = f"""
Create a practical, beginner-friendly 7-day fitness plan for {username}.
Age: {age}; weight: {weight} kg; goal: {goal.replace('_', ' ')}; intensity: {intensity}.
Use a clear day-by-day format. For each day include focus, warm-up, main activity with sets/reps or duration,
cool-down/recovery, and an easier alternative. Include rest/recovery days. Avoid extreme exercise,
promises of weight change, and medical claims. Tell the user to stop if they feel pain or dizziness.
Adapt intensity conservatively and do not assume access to gym equipment. Keep the response readable.
This is general wellness information, not medical advice.
"""
    try:
        return _generate(prompt, WORKOUT_MODEL), False
    except Exception:
        return demo_workout(goal, intensity), True

def generate_tip(goal: str) -> tuple[str, bool]:
    prompt = f"Give one concise, safe nutrition or recovery tip for the fitness goal '{goal.replace('_', ' ')}'. Avoid calorie prescriptions, supplements, and medical claims. Mention balanced meals, hydration, sleep, or recovery where relevant. Under 90 words."
    try:
        return _generate(prompt, TIP_MODEL), False
    except Exception:
        tips = {
            "muscle_gain": "Include a variety of protein-rich foods (such as beans, eggs, dairy, fish, or tofu) alongside carbohydrates, vegetables, and enough fluids. Sleep and recovery matter too.",
            "weight_loss": "Build balanced meals around vegetables or fruit, protein-rich foods, whole grains, and water. Avoid crash diets; sustainable habits and adequate sleep are more useful than extreme restriction.",
            "flexibility": "Drink water regularly and pair gentle mobility work with balanced meals. Move gradually and never force a stretch into pain.",
            "general_wellness": "Aim for regular balanced meals, water throughout the day, and a consistent sleep routine to support everyday activity and recovery."
        }
        return tips.get(goal, tips["general_wellness"]), True

def update_workout(original_plan: str, feedback: str, goal: str, intensity: str) -> tuple[str, bool]:
    prompt = f"""
Revise this general 7-day fitness plan using the user's feedback. Preserve the goal ({goal.replace('_', ' ')})
and preferred intensity ({intensity}); prioritize safety, recovery, and practical alternatives.
Do not follow feedback that requests dangerous or extreme exercise. Explain briefly if a request cannot be safely followed.
Original plan:
{original_plan[:12000]}
User feedback:
{feedback}
Return the complete revised 7-day plan with warm-up, activity, cool-down/recovery and rest days.
"""
    try:
        return _generate(prompt, WORKOUT_MODEL), False
    except Exception:
        return original_plan + "\n\nLocal fallback note: Your feedback was saved, but AI revision was unavailable. Try again after configuring a valid Gemini API key.", True

def demo_workout(goal: str, intensity: str) -> str:
    level = {"low": "gentle 10–20 minute movement", "medium": "moderate 20–30 minute movement", "high": "challenging but controlled 25–35 minute movement"}[intensity]
    focus = {
        "weight_loss": ["Brisk walking", "Full-body basics", "Low-impact cardio", "Mobility and walking", "Strength basics", "Enjoyable cardio", "Rest and gentle stretching"],
        "muscle_gain": ["Full-body strength", "Walk and mobility", "Upper-body basics", "Recovery walk", "Lower-body basics", "Light full-body practice", "Rest"],
        "flexibility": ["Full-body mobility", "Gentle yoga", "Hip and shoulder mobility", "Easy walk", "Full-body stretching", "Balance and mobility", "Rest"],
        "general_wellness": ["Full-body movement", "Walk and mobility", "Bodyweight basics", "Recovery walk", "Cardio of choice", "Gentle strength", "Rest"]
    }.get(goal, ["Full-body movement", "Walk and mobility", "Bodyweight basics", "Recovery walk", "Cardio of choice", "Gentle strength", "Rest"])
    lines = ["DEMO MODE — configure GOOGLE_API_KEY to use Gemini. This sample is general guidance, not medical advice.\n"]
    for i, day in enumerate(focus, 1):
        activity = "Rest or easy stretching" if day == "Rest" else f"{level}: {day}; choose movements you can do comfortably."
        lines.append(f"DAY {i} — {day}\nWarm-up: 5 minutes of easy movement.\nMain activity: {activity}\nCool-down: 3–5 minutes easy movement and comfortable stretching. Stop if you feel pain, dizziness, or unusual shortness of breath.\n")
    return "\n".join(lines)
