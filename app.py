import os
from flask import Flask, session, request, jsonify, abort
from flask import render_template
from eudoxa import EudoxaManager

app = Flask(__name__)

# -----------------------------------------------------------
#  SESSION / CONFIG
# -----------------------------------------------------------
# Viktigt: hemlighet för att kunna använda Flask-sessioner
app.secret_key = os.getenv("SECRET_KEY") or "dev-secret-change-me"


# -----------------------------------------------------------
#  HJÄLPFUNKTIONER
# -----------------------------------------------------------
def load_manager_or_400():
    """Läs EudoxaManager från sessionen eller returnera 400."""
    data = session.get("manager")
    if not data:
        abort(400, description="No active project")
    return EudoxaManager.from_dict(data)


def save_manager(mgr: EudoxaManager):
    """Spara manager i sessionen."""
    session["manager"] = mgr.to_dict()


# -----------------------------------------------------------
#  UI – valfritt (används om du vill köra index.html)
# -----------------------------------------------------------
@app.get("/")
def index():
    return render_template("index.html", project_name=session.get("project_name"))

# -----------------------------------------------------------
#  REST: PROJECT
# -----------------------------------------------------------

@app.post("/api/project")
def create_project():
    """Skapa nytt projekt (endast om inget projekt redan finns)."""
    if "project_name" in session:
        return {"error": "A project already exists. Use PUT to rename."}, 409

    data = request.get_json(silent=True) or {}
    name = (data.get("project_name") or "").strip()

    if not name:
        return {"error": "Project name must be non-empty."}, 400

    mgr = EudoxaManager()

    session["project_name"] = name
    save_manager(mgr)

    return {"message": "Project created", "project_name": name}, 201

@app.put("/api/project")
def rename_project():
    """Byt namn på ett befintligt projekt."""
    if "project_name" not in session:
        return {"error": "No active project. Use POST to create a project."}, 404

    data = request.get_json(silent=True) or {}
    name = (data.get("project_name") or "").strip()

    if not name:
        return {"error": "Project name must be non-empty."}, 400

    session["project_name"] = name

    return {"message": "Project renamed", "project_name": name}, 200

@app.get("/api/project")
def get_project():
    """Hämta projektets namn + serialiserad EudoxaManager."""
    name = session.get("project_name")
    data = session.get("manager")

    if not name or not data:
        return {"error": "No active project"}, 404

    return {
        "project_name": name,
        "manager": data
    }, 200


@app.delete("/api/project")
def delete_project():
    """Radera projekt + manager ur sessionen."""
    session.pop("project_name", None)
    session.pop("manager", None)
    return "", 204


# -----------------------------------------------------------
#  REST: ASPECTS
# -----------------------------------------------------------
@app.post("/api/aspects")
def add_aspect():
    mgr = load_manager_or_400()

    data = request.get_json()
    name = data["name"]
    data_type = data["data_type"]
    description = data.get("description")

    try:
        mgr.add_aspect(name, data_type, description)
    except Exception as e:
        return {"error": str(e)}, 400

    save_manager(mgr)
    return {"message": "Aspect added"}, 201


# -----------------------------------------------------------
#  REST: LEVELS
# -----------------------------------------------------------
@app.post("/api/aspects/<aspect_name>/levels")
def add_level(aspect_name):
    mgr = load_manager_or_400()
    data = request.get_json()

    level = data["level"]
    description = data.get("description")

    try:
        mgr.add_aspect_level(aspect_name, level, description)
    except Exception as e:
        return {"error": str(e)}, 400

    save_manager(mgr)
    return {"message": "Level added"}, 201


# -----------------------------------------------------------
#  REST: CONSEQUENCES
# -----------------------------------------------------------
@app.post("/api/consequences")
def add_consequence():
    mgr = load_manager_or_400()

    data = request.get_json()
    short = data["short_name"]
    levels = data["aspect_levels"]

    try:
        mgr.add_consequence(short, levels)
    except Exception as e:
        return {"error": str(e)}, 400

    save_manager(mgr)
    return {"message": "Consequence added"}, 201


# -----------------------------------------------------------
#  TESTPANEL
# -----------------------------------------------------------
@app.get("/testpanel")
def testpanel():
    return render_template("testpanel.html")


# -----------------------------------------------------------
#  STARTA SERVERN
# -----------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)