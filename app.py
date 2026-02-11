from flask import Flask
app = Flask(__name__)
app.secret_key = "Silmantra!"

@app.route("/")
def index():
    count = session.get("count", 0)
    count += 1
    session["count"] = count
    return f"Du har laddat sidan {count} gånger i denna session."

# OBS: kör INTE app.run() på PythonAnywhere
if __name__ == "__main__":
    app.run(debug=True)
