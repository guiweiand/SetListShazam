from flask import Flask, render_template, request
from main import run

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/process_url", methods=["POST"])
def process_url():
    url = request.form["url"]
    setlist_string = run(URL=url)
    return render_template("index.html", url=url, setlist=setlist_string)

if __name__ == "__main__":
    app.run(debug=True)