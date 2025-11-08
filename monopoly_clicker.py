from flask import Flask, render_template, jsonify, request
import threading, time, json, os

app = Flask(__name__)

# --- Player State ---
DATA_FILE = "player_data.json"

default_data = {
    "money": 0,
    "income_per_sec": 0,
    "properties": []
}

# Property list (cost & income)
PROPERTIES = [
    {"name": "Mediterranean Ave", "cost": 100, "income": 1},
    {"name": "Baltic Ave", "cost": 250, "income": 3},
    {"name": "Oriental Ave", "cost": 500, "income": 7},
    {"name": "Boardwalk", "cost": 1000000, "income": 5000},
]

# --- Load/Save System ---
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    else:
        return default_data.copy()

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

player_data = load_data()

# --- Passive Income Thread ---
def passive_income():
    while True:
        time.sleep(1)
        player_data["money"] += player_data["income_per_sec"]
        save_data(player_data)

threading.Thread(target=passive_income, daemon=True).start()

# --- Routes ---
@app.route("/")
def index():
    return render_template("index.html", properties=PROPERTIES)

@app.route("/click", methods=["POST"])
def click():
    player_data["money"] += 1
    save_data(player_data)
    return jsonify(player_data)

@app.route("/buy", methods=["POST"])
def buy():
    prop_name = request.json.get("property")
    prop = next((p for p in PROPERTIES if p["name"] == prop_name), None)

    if not prop:
        return jsonify({"error": "Invalid property"}), 400

    if prop["name"] in player_data["properties"]:
        return jsonify({"error": "Already owned"}), 400

    if player_data["money"] >= prop["cost"]:
        player_data["money"] -= prop["cost"]
        player_data["income_per_sec"] += prop["income"]
        player_data["properties"].append(prop["name"])
        save_data(player_data)
        return jsonify(player_data)
    else:
        return jsonify({"error": "Not enough money"}), 400

@app.route("/status")
def status():
    return jsonify(player_data)

if __name__ == "__main__":
    app.run(debug=True)
