import os
from flask import Flask, render_template, request, session, jsonify

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")


# ---------------------------------------------------------
# UI (icke-REST)
# ---------------------------------------------------------

@app.get("/")
def index():
    return render_template("index.html", project_name=session.get("project_name"))


# ---------------------------------------------------------
# REST API
# ---------------------------------------------------------

@app.get("/api/project")
def api_get_project():
    """Returnera projektets namn (om något finns)."""
    name = session.get("project_name")
    if not name:
        return jsonify({"project_name": None}), 404
    return jsonify({"project_name": name})


@app.put("/api/project")
def api_set_project():
    """Sätt projektets namn."""
    data = request.get_json(silent=True) or {}
    name = (data.get("project_name") or "").strip()

    if not name:
        return jsonify({"error": "Project name must be non-empty."}), 400

    session["project_name"] = name
    return jsonify({"message": "Project name updated.", "project_name": name}), 200


@app.delete("/api/project")
def api_delete_project():
    """Ta bort projektets namn från sessionen."""
    session.pop("project_name", None)
    return jsonify({"message": "Project deleted."}), 204


# ---------------------------------------------------------
# Start
# ---------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)