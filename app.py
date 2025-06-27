import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fejlesztesi_kulcs')

# Adatbázis URI környezeti változóból (Render), vagy fallback SQLite-ra
db_uri = os.environ.get('DATABASE_URL', 'sqlite:///news.db')
if db_uri.startswith("postgres://"):
    db_uri = db_uri.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Egyszerű bejelentkezési adatok
admin_user = os.environ.get('ADMIN_USER', 'admin')
admin_pass = os.environ.get('ADMIN_PASS', 'jelszo123')

# Adatbázis modell
class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    latest = News.query.order_by(News.date.desc()).first()
    return render_template('index.html', latest=latest)

@app.route('/news')
def news():
    page = int(request.args.get('page', 1))
    per_page = 10
    news_items = News.query.order_by(News.date.desc()).paginate(page=page, per_page=per_page)
    return render_template('news.html',
                           news=news_items.items,
                           page=page,
                           total_pages=news_items.pages)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] == admin_user and request.form['password'] == admin_pass:
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            error = 'Hibás felhasználónév vagy jelszó.'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        new_post = News(title=title, content=content)
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('news'))
    return render_template('admin.html')

@app.route('/delete/<int:news_id>', methods=['POST'])
def delete_news(news_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    news_item = News.query.get_or_404(news_id)
    db.session.delete(news_item)
    db.session.commit()
    return redirect(url_for('news'))


if __name__ == '__main__':
    app.run(debug=True)
