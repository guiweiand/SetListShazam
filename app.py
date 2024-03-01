from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/process_url", methods=["POST"])
def process_url():
    url = request.form["url"]
    # Seu script Python para processar o URL
    string_retornada = "Sua string retornada"
    return render_template("index.html", url=url, string_retornada=string_retornada)

if __name__ == "__main__":
    app.run(debug=True)