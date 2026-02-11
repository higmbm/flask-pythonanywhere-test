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
            # Läs Excel. dtype=object gör att vi inte oavsiktligt tvingar blandade kolumner till float.
            df = pd.read_excel(f, engine="openpyxl", dtype=object)

            # Ersätt NaN/None med tom sträng i hela DF:
            df = df.where(df.notna(), "")

            # Rendera till HTML och säkerställ att eventuell kvarvarande NaN visas som tomt
            table_html = df.to_html(classes="table table-striped",
                                    index=False,
                                    na_rep="")  # extra säkerhetslina
        except Exception as e:
            table_html = f"<p>Kunde inte läsa filen: {e}</p>"

    return render_template("index.html", table_html=table_html)

if __name__ == "__main__":
    app.run(debug=True)
