from extensions import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(80), nullable=False)
    games = db.Column(db.UnicodeText, nullable=False)

    def get_games(self):
        if len(self.games) == 0:
            return []
        return list(self.games.split(','))

    def __repr__(self):
        dic = {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "password": self.password.decode("utf-8"),
            "games": list(self.games.split(","))
        }
        return str(dic)


class Seller(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    stripe_account_id = db.Column(db.String(100), unique=True, nullable=False)
    authorized = db.Column(db.Boolean, nullable=False)

    def __repr__(self):
        return str({"id": self.id, "user_id": self.user_id, "stripe_account_id": self.stripe_account_id})


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    serial_id = db.Column(db.String(32), nullable=False)

    stripe_account_id = db.Column(db.String(100), unique=True, nullable=False)
    stripe_product_id = db.Column(db.String(100), unique=True, nullable=False)
    stripe_price_id = db.Column(db.String(100), unique=True, nullable=False)

    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    price = db.Column(db.Integer, nullable=False)

    rom_name = db.Column(db.String(50), nullable=False)
    image_name = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        dic = {
            "id": self.id,
            "user_id": self.user_id,
            "serial_id": self.serial_id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "rom_name": self.rom_name,
            "image_name": self.image_name
        }
        return str(dic)
