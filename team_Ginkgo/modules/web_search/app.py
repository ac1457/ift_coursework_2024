from flask import Flask, render_template, request
import requests
import os

app = Flask(__name__)

# FastAPI API address
API_URL = os.getenv("API_URL", "http://localhost:8000/report")


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    if request.method == "POST":
        company = request.form["company"]
        year = request.form["year"]

        try:
            year = int(year)
        except ValueError:
            return render_template("index.html", result={"message": "Invalid year format, please enter a valid year"})

        # Call FastAPI query API
        try:
            response = requests.get(f"{API_URL}?query={company}&year={year}")
            if response.status_code == 200:
                result = response.json()
            else:
                result = {"message": f"API query failed, error code: {response.status_code}"}
        except requests.exceptions.RequestException:
            result = {"message": "Unable to connect to API server"}

    return render_template("index.html", result=result)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
