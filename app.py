from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3, re, hashlib, os

app = Flask(__name__)
app.secret_key = "your_secret_key"

# ---------------------- DEBUG INFO ----------------------
print("✅ Flask is starting...")
print("💾 Working directory:", os.getcwd())
db_path = os.path.join(os.getcwd(), "travel_budget.db")
print("📂 Database path will be:", db_path)

# ---------------------- DATABASE SETUP ----------------------
def init_db():
    """Create the database and users table if not exists."""
    conn = sqlite3.connect(db_path)
    conn.execute('''CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')
    conn.commit()
    conn.close()
    print("📘 Database initialized successfully!")

init_db()

# ---------------------- PASSWORD HASHING ----------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ---------------------- ROUTES ----------------------

# ✅ MAIN HOME ROUTE
@app.route('/')
def home():
    return render_template('index.html')

# ✅ Redirect /index → /
@app.route('/index')
def index_redirect():
    return redirect(url_for('home'))

# ---------- REGISTER ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        print("📝 Registration Attempt:", name, email)

        # --- Validation checks ---
        if not re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', email):
            msg = '❌ Invalid email format!'
        elif len(password) < 8:
            msg = '❌ Password must be at least 8 characters!'
        elif not name:
            msg = '❌ Name cannot be empty!'
        else:
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE email=?", (email,))
                existing = cursor.fetchone()

                if existing:
                    msg = '⚠️ Account already exists!'
                    print("⚠️ Account already exists for:", email)
                else:
                    hashed_pw = hash_password(password)
                    cursor.execute(
                        "INSERT INTO users(name, email, password) VALUES (?, ?, ?)",
                        (name, email, hashed_pw)
                    )
                    conn.commit()
                    print("✅ User inserted and committed to DB:", email)
                    flash('Registration successful! Please log in.')
                    conn.close()
                    return redirect(url_for('login'))
            except Exception as e:
                msg = f'❌ Database error: {e}'
                print("❌ Error inserting user:", e)
            finally:
                conn.close()

    return render_template('register.html', msg=msg)

# ---------- LOGIN ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        hashed_pw = hash_password(password)

        print("🔐 Login attempt for:", email)

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email=? AND password=?", (email, hashed_pw))
            account = cursor.fetchone()
            conn.close()

            if account:
                session['loggedin'] = True
                session['user'] = account[1]
                print("✅ Login successful for:", email)
                flash(f"Welcome back, {account[1]}!")
                return redirect(url_for('home'))
            else:
                msg = '❌ Incorrect email or password!'
                print("⚠️ Login failed for:", email)
        except Exception as e:
            msg = f'❌ Database error: {e}'
            print("❌ Error during login:", e)

    return render_template('login.html', msg=msg)

# ---------- LOGOUT ----------
@app.route('/logout')
def logout():
    print("👋 User logged out")
    session.clear()
    flash('Logged out successfully.')
    return redirect(url_for('home'))

# ---------- CALCULATOR ----------
@app.route('/calculator')
def calculator_page():
    return render_template('calculator.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        destination = request.form['destination']
        people = int(request.form['people'])
        days = int(request.form['days'])
        stay = int(request.form['stay'])
        mode = int(request.form['mode'])
        total = (stay * days * people) + (mode * people)
        print(f"💰 Calculation: {destination} -> ₹{total}")
        return render_template('calculator.html', total=total, destination=destination)
    except Exception as e:
        print("❌ Error in calculation:", e)
        flash('Error calculating budget. Please try again.')
        return redirect(url_for('calculator_page'))

# ---------- STATIC PAGES ----------
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

# ---------- 404 HANDLER ----------
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# ---------------------- MAIN ----------------------
if __name__ == '__main__':
    app.run(debug=True)
