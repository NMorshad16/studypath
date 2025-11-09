from flask import Flask, render_template, request, jsonify
from datetime import date, timedelta
from dateutil.parser import parse as dtparse
import os, json

app = Flask(__name__)

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "studypath.json")

def load_data():
    if not os.path.exists(DATA_PATH):
        return {"profile": {}, "plan": [], "progress": {}}
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"profile": {}, "plan": [], "progress": {}}

def save_data(payload):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

def daterange(start, end):
    cur = start
    while cur <= end:
        yield cur
        cur = cur + timedelta(days=1)

def generate_plan(subjects, exam_date_str, hours_per_day, weaknesses):
    today = date.today()
    exam_date = dtparse(exam_date_str).date()
    if exam_date <= today:
        exam_date = today

    weakset = set([s.strip().lower() for s in weaknesses])
    weights = {s: 1.0 + (1.0 if s.strip().lower() in weakset else 0.0) for s in subjects}
    total_weight = sum(weights.values()) or 1.0

    sessions_per_day = max(1, int(round(float(hours_per_day))))
    days = list(daterange(today, exam_date))

    # build empty plan skeleton
    plan = [{"date": d.isoformat(), "tasks": []} for d in days]

    total_sessions = len(days) * sessions_per_day
    # target count per subject proportionally to weights
    target = {s: max(1, int(round(total_sessions * (weights[s]/total_weight)))) for s in subjects}

    # rounding fix
    diff = total_sessions - sum(target.values())
    subs_sorted = sorted(subjects, key=lambda s: -weights[s])
    i = 0
    while diff != 0 and subs_sorted:
        s = subs_sorted[i % len(subs_sorted)]
        if diff > 0:
            target[s] += 1; diff -= 1
        else:
            if target[s] > 1:
                target[s] -= 1; diff += 1
        i += 1

    remaining = target.copy()
    rots = list(subjects)
    si = 0
    for day in plan:
        for _ in range(sessions_per_day):
            picked = None
            for s in subs_sorted:  # prefer weak first via sort
                if remaining.get(s, 0) > 0:
                    picked = s; break
            if not picked:
                for s in rots:
                    if remaining.get(s, 0) > 0:
                        picked = s; break
            if not picked:
                picked = rots[si % len(rots)]
            remaining[picked] = max(0, remaining.get(picked, 0) - 1)
            day["tasks"].append({
                "subject": picked,
                "duration_hours": round(float(hours_per_day)/sessions_per_day, 2),
                "status": "pending"
            })
        si += 1

    return plan

@app.route("/")
def index():
    data = load_data()
    return render_template("index.html", data=data)

@app.route("/api/generate", methods=["POST"])
def api_generate():
    body = request.get_json(force=True)
    subjects = [s.strip() for s in body.get("subjects", []) if s.strip()]
    exam_date = body.get("exam_date")
    hours = float(body.get("hours_per_day", 2))
    weaknesses = [w.strip() for w in body.get("weaknesses", []) if w.strip()]

    if not subjects or not exam_date:
        return jsonify({"ok": False, "error": "Please provide subjects and exam date."}), 400

    data = load_data()
    data["profile"] = {
        "subjects": subjects,
        "exam_date": exam_date,
        "hours_per_day": hours,
        "weaknesses": weaknesses
    }
    data["plan"] = generate_plan(subjects, exam_date, hours, weaknesses)
    done = 0
    total = sum(len(d["tasks"]) for d in data["plan"])
    data["progress"] = {"done": done, "total": total}
    save_data(data)
    return jsonify({"ok": True, "plan": data["plan"], "progress": data["progress"]})

@app.route("/api/plan", methods=["GET"])
def api_plan():
    data = load_data()
    return jsonify({"ok": True, "plan": data.get("plan", []), "profile": data.get("profile", {}), "progress": data.get("progress", {})})

@app.route("/api/complete", methods=["POST"])
def api_complete():
    body = request.get_json(force=True)
    date_str = body.get("date")
    idx = int(body.get("index", -1))
    data = load_data()
    for day in data.get("plan", []):
        if day["date"] == date_str and 0 <= idx < len(day["tasks"]):
            if day["tasks"][idx]["status"] != "done":
                day["tasks"][idx]["status"] = "done"
                data["progress"]["done"] = data["progress"].get("done", 0) + 1
            break
    save_data(data)
    return jsonify({"ok": True, "progress": data["progress"]})

@app.route("/api/reset", methods=["POST"])
def api_reset():
    data = {"profile": {}, "plan": [], "progress": {}}
    save_data(data)
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(debug=True)
