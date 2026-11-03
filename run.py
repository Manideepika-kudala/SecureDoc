from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "<h1>Welcome to SecureDoc</h1><p>Your secure document management website.</p>"

if __name__ == "__main__ ":
    app.run(debug=True)
