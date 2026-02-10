from flask import Flask
app = Flask(__name__)

@app.route("/")
def index():
    return "Hello from Flask on PythonAnywhere!"

# OBS: kör INTE app.run() på PythonAnywhere
if __name__ == "__main__":
    app.run(debug=True)
