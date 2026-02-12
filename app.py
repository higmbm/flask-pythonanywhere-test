import sys, os

from flask import Flask, render_template, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        project_name = (request.form.get("project_name") or "").strip()
        if project_name:
            session["project_name"] = project_name
            return redirect(url_for("index"))
        else:
            return render_template("index.html", error="Project name must be non-empty.", project_name=None)

    return render_template("index.html", project_name=session.get("project_name"))

if __name__ == "__main__":
    app.run(debug=True)
