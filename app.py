from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///bets.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

starting_bankroll = 100000


class Bet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event = db.Column(db.String(200), nullable=False)
    pick = db.Column(db.String(200), nullable=False)
    odds = db.Column(db.Float, nullable=False)
    stake = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    profit = db.Column(db.Float, nullable=False)


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    bets = Bet.query.order_by(Bet.id.desc()).all()

    total_profit = sum(bet.profit for bet in bets)
    current_bankroll = starting_bankroll + total_profit

    wins = sum(1 for bet in bets if bet.status == "win")
    losses = sum(1 for bet in bets if bet.status == "loss")
    pending = sum(1 for bet in bets if bet.status == "pending")

    settled = wins + losses
    total_stake = sum(bet.stake for bet in bets if bet.status in ["win", "loss"])

    win_rate = round((wins / settled) * 100, 2) if settled > 0 else 0
    roi = round((total_profit / total_stake) * 100, 2) if total_stake > 0 else 0

    return render_template(
        "index.html",
        bets=bets,
        starting_bankroll=starting_bankroll,
        current_bankroll=round(current_bankroll, 2),
        total_profit=round(total_profit, 2),
        wins=wins,
        losses=losses,
        pending=pending,
        win_rate=win_rate,
        roi=roi
    )


@app.route("/add", methods=["POST"])
def add_bet():
    event = request.form.get("event", "").strip()
    pick = request.form.get("pick", "").strip()
    status = request.form.get("status", "pending").strip()

    try:
        odds = float(request.form.get("odds", 0))
        stake = float(request.form.get("stake", 0))
    except ValueError:
        return redirect("/")

    if not event or not pick:
        return redirect("/")

    if status == "win":
        profit = (odds * stake) - stake
    elif status == "loss":
        profit = -stake
    else:
        profit = 0

    new_bet = Bet(
        event=event,
        pick=pick,
        odds=odds,
        stake=stake,
        status=status,
        profit=round(profit, 2)
    )

    db.session.add(new_bet)
    db.session.commit()

    return redirect("/")


@app.route("/delete/<int:bet_id>")
def delete_bet(bet_id):
    bet = Bet.query.get(bet_id)
    if bet:
        db.session.delete(bet)
        db.session.commit()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)