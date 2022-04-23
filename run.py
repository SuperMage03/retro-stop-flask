import os
from app import app
from extensions import db


def setup_db(app):
    if not os.path.exists(os.path.join(os.getcwd(), app.config["DB_NAME"])):
        db.create_all()


if __name__ == '__main__':
    with app.app_context():
        setup_db(app)

    app.run(debug=True)
