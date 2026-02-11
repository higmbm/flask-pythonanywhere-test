from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    table_html = None

    if request.method == "POST":
        if "excelfile" not in request.files:
            return render_template("index.html", table_html="<p>Ingen fil vald.</p>")

        f = request.files["excelfile"]
        if f.filename == "":
            return render_template("index.html", table_html="<p>Filnamnet är tomt.</p>")

        try:
            # Läs Excel-arket till pandas DataFrame
            df = pd.read_excel(f, engine="openpyxl")

            # Gör om DataFrame till HTML-tabell
            table_html = df.to_html(classes="table table-striped", index=False)
        except Exception as e:
            table_html = f"<p>Kunde inte läsa filen: {e}</p>"

    return render_template("index.html", table_html=table_html)

if __name__ == "__main__":
    app.run(debug=True)
