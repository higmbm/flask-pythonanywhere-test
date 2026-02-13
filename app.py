import os, sys

from flask import Flask, render_template, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

@app.get("/")
def index_get():
    return render_template("index.html", project_name=session.get("project_name"))

@app.post("/")
def index_post():
    project_name = (request.form.get("project_name") or "").strip()
    if not project_name:
        # Rendera med 400-status för tydlig validering
        return render_template(
            "index.html",
            error="Project name must be non-empty.",
            project_name=None
        ), 400
    session["project_name"] = project_name
    return redirect(url_for("index_get"))

@app.post("/delete-project")
def delete_project():
    # Ta bort värdet om det finns
    session.pop("project_name", None)
    # (valfritt) nollställ permanent-flaggan: session.permanent = False
    return redirect(url_for("index_get"))

if __name__ == "__main__":
    app.run(debug=True)
