from flask import Flask, render_template
from models import db

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


@app.route("/")
def index():
    """
    Render the application's home page.
    
    Returns:
        str: Rendered 'index.html' template for the root URL.
    """
    return render_template("index.html")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
