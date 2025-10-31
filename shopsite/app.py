from flask import Flask, jsonify, render_template, redirect, session, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # change this to something secure


# ---------- SQLite Connection ----------
def get_db_connection():
    conn = sqlite3.connect("data_wrong/handmade_store.db")
    conn.row_factory = sqlite3.Row
    return conn


# ---------- Auto-create DB + Tables ----------
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        image_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        total_amount REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'Pending',
        tracking_number TEXT,
        shipping_provider TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_name TEXT,
        price REAL NOT NULL,
        qty INTEGER NOT NULL,
        subtotal REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(id)
    );
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized!")


if not os.path.exists("handmade_store.db"):
    print("🔧 Creating handmade_store.db...")
    init_db()


# ---------- Flask-Login Setup ----------
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


class User(UserMixin):
    def __init__(self, id, name, email, password_hash):
        self.id = id
        self.name = name
        self.email = email
        self.password_hash = password_hash


@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return User(user["id"], user["name"], user["email"], user["password_hash"])
    return None


# ---------- Authentication ----------
@app.route("/", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cursor.fetchone()
        conn.close()
        if user and check_password_hash(user["password_hash"], password):
            login_user(User(user["id"], user["name"], user["email"], user["password_hash"]))
            return redirect(url_for("index"))
        else:
            flash("Invalid email or password", "danger")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        password_hash = generate_password_hash(password)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, password_hash)
            )
            conn.commit()
            conn.close()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Email already exists!", "danger")
    return render_template("register.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# ---------- Profile ----------
@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html", user=current_user)


@app.route("/edit-profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_db_connection()
        cursor = conn.cursor()

        if username:
            cursor.execute("UPDATE users SET name=? WHERE id=?", (username, current_user.id))
        if email:
            cursor.execute("UPDATE users SET email=? WHERE id=?", (email, current_user.id))
        if password:
            new_hash = generate_password_hash(password)
            cursor.execute("UPDATE users SET password_hash=? WHERE id=?", (new_hash, current_user.id))

        conn.commit()
        conn.close()

        flash("Profile updated successfully!", "success")
        return redirect(url_for("profile"))

    return render_template("edit_profile.html", user=current_user)


# ---------- Main Pages ----------
@app.route("/index")
@login_required
def index():
    return render_template("index.html")


@app.route("/about")
@login_required
def about():
    return render_template("about.html")


@app.route("/contact")
@login_required
def contact():
    return render_template("contact.html")


@app.route("/blog")
@login_required
def blog():
    return render_template("blog.html")


@app.route("/shop")
@login_required
def shop():
    return render_template("shop.html")


# ---------- Product Categories ----------
@app.route("/assorted-craft")
@login_required
def assorted_craft():
    return render_template("assorted-craft.html")


@app.route("/blue-pottery")
@login_required
def blue_pottery():
    return render_template("blue-pottery.html")


@app.route("/brass-craft")
@login_required
def brass_craft():
    return render_template("brass-craft.html")


@app.route("/crystal-craft")
@login_required
def crystal_craft():
    return render_template("crystal-craft.html")


@app.route("/furniture")
@login_required
def furniture():
    return render_template("furniture.html")


@app.route("/marble-handicrafts")
@login_required
def marble_handicrafts():
    return render_template("marble-handicrafts.html")


@app.route("/metal-craft")
@login_required
def metal_craft():
    return render_template("metal-craft.html")


@app.route("/painting")
@login_required
def painting():
    return render_template("painting.html")


@app.route("/wooden-handicrafts")
@login_required
def wooden_handicrafts():
    return render_template("wooden-handicrafts.html")


# ---------- Error ----------
@app.errorhandler(404)
def custom_404(e):
    return redirect(url_for("login"))


# ---------- Cart ----------
@app.route("/cart")
@login_required
def cart():
    cart = session.get("cart", [])
    total = sum(item["price"] * item["qty"] for item in cart)
    return render_template("cart.html", cart=cart, total=total)


@app.route("/add-to-cart/<product_name>", methods=["POST"])
@login_required
def add_to_cart(product_name):
    data = request.get_json() or {}
    try:
        price = float(data.get("price", 0.0))
    except (ValueError, TypeError):
        price = 0.0

    image = data.get("image")
    cart = session.get("cart", [])

    for item in cart:
        if item["name"] == product_name:
            item["qty"] += 1
            break
    else:
        cart.append({"name": product_name, "price": price, "qty": 1, "image": image})

    session["cart"] = cart
    session.modified = True

    return jsonify({
        "success": True,
        "message": f"{product_name} added to cart!",
        "cart_count": sum(i["qty"] for i in cart)
    })


@app.route("/clear-cart")
@login_required
def clear_cart():
    session.pop("cart", None)
    flash("Cart cleared!", "info")
    return redirect(url_for("index"))


# ---------- Checkout ----------
@app.route("/checkout", methods=["POST"])
@login_required
def checkout():
    cart = session.get("cart", [])
    selected_items = request.form.getlist("selected_items")

    if not selected_items:
        flash("Please select at least one item to proceed!", "warning")
        return redirect(url_for("cart"))

    selected_items = [int(i) for i in selected_items]
    checkout_items = [cart[i] for i in selected_items if i < len(cart)]
    total = sum(item["price"] * item["qty"] for item in checkout_items)

    return render_template("checkout.html", cart=checkout_items, total=total)


@app.route("/remove_item/<int:product_index>", methods=["POST"])
@login_required
def remove_item(product_index):
    cart = session.get("cart", [])
    if 0 <= product_index < len(cart):
        removed_item = cart.pop(product_index)
        session["cart"] = cart
        flash(f"Removed {removed_item['name']} from cart", "success")
    else:
        flash("Invalid item selected", "danger")
    return redirect(url_for("cart"))


# ---------- Place Order ----------
@app.route("/place_order", methods=["POST"])
@login_required
def place_order():
    cart = session.get("cart", [])

    if not cart:
        return "Cart is empty", 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        total_amount = sum(item["price"] * item["qty"] for item in cart)

        cursor.execute(
            "INSERT INTO orders (user_id, total_amount, created_at) VALUES (?, ?, datetime('now'))",
            (current_user.id, total_amount)
        )
        order_id = cursor.lastrowid

        for item in cart:
            subtotal = item["price"] * item["qty"]
            cursor.execute(
                "INSERT INTO order_items (order_id, product_name, price, qty, subtotal) VALUES (?, ?, ?, ?, ?)",
                (order_id, item["name"], item["price"], item["qty"], subtotal)
            )

        conn.commit()
        conn.close()
        session["cart"] = []

        return redirect(url_for("my_orders"))
    except Exception as e:
        print("Error placing order:", e)
        return f"Error placing order: {str(e)}", 500


# ---------- My Orders ----------
@app.route("/my-orders")
@login_required
def my_orders():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT o.id, o.total_amount, o.created_at, o.status,
                   o.tracking_number, o.shipping_provider,
                   i.product_name, i.price, i.qty, i.subtotal
            FROM orders o
            LEFT JOIN order_items i ON o.id = i.order_id
            WHERE o.user_id=?
            ORDER BY o.created_at DESC, i.id ASC
        """, (current_user.id,))

        rows = cursor.fetchall()
        conn.close()

        orders_dict = {}
        for row in rows:
            oid = row["id"]
            if oid not in orders_dict:
                orders_dict[oid] = {
                    "id": oid,
                    "total": row["total_amount"],
                    "created_at": row["created_at"],
                    "status": row["status"],
                    "tracking_number": row["tracking_number"],
                    "shipping_provider": row["shipping_provider"],
                    "order_items": []
                }
            if row["product_name"]:
                orders_dict[oid]["order_items"].append({
                    "product_name": row["product_name"],
                    "price": row["price"],
                    "quantity": row["qty"],
                    "subtotal": row["subtotal"]
                })

        return render_template("my_orders.html", orders=list(orders_dict.values()))
    except Exception as e:
        print("Error fetching orders:", str(e))
        return f"Error fetching orders: {str(e)}", 500


@app.route("/cart/update/<int:product_index>/<action>", methods=["POST"])
def update_cart(product_index, action):
    cart = session.get("cart", [])
    if 0 <= product_index < len(cart):
        if action == "increase":
            cart[product_index]["qty"] += 1
        elif action == "decrease" and cart[product_index]["qty"] > 1:
            cart[product_index]["qty"] -= 1
    session["cart"] = cart
    return redirect(url_for("cart"))


# ---------- Run ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000,debug=True)
