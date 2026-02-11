from flask import Flask, session, request

app = Flask(__name__)
app.secret_key = "Silmantra!"   # krävs för sessioner

@app.route("/")
def index():
    count = session.get("count", 0)
    count += 1
    session["count"] = count
    return f"TEST: Du har laddat sidan {count} gånger i denna session."

if __name__ == "__main__":
    app.run(debug=True)
