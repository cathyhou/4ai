from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from data import Articles
from flaskext.mysql import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from pymysql.cursors import DictCursor
from functools import wraps

app = Flask(__name__)

#config mysql
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'chou1212'
app.config['MYSQL_DATABASE_DB'] = 'appuser'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
#init mysql
mysql = MySQL(cursorclass=DictCursor)
mysql.init_app(app)

Articles = Articles()


@app.route('/')
def index():
    return render_template('home.html')


@app.route('/impact')
def impact():
    return render_template('impact.html')


@app.route('/services')
def services():
    return render_template("services.html")


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/donate')
def donate():
    return render_template('donate.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/articles')
def articles():
    return render_template('articles.html', articles=Articles)


@app.route('/article/<string:id>/')
def article(id):
    return render_template('article.html', id=id)


class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        conn=mysql.connect()
        cur = conn.cursor()
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s,%s,%s,%s)", (name, email, username, password))
        conn.commit()
        cur.close()

        flash('You are now registered and can log in', 'success')
        return redirect(url_for('index'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']
        conn = mysql.connect()
        cur = conn.cursor()

        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])
        if result > 0:
            data = cur.fetchone()
            password = data['password']

            if sha256_crypt.verify(password_candidate, password):
                session['logged_in']= True
                session['username'] = username
                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid Login'
                return render_template('login.html', error=error)
            cur.close()
        else:
            error = 'Username Not Found'
            return render_template('login.html', error=error)
    return render_template('login.html')


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap


@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))


@app.route('/dashboard')
@is_logged_in
def dashboard():
    return render_template('dashboard.html')


@app.route('/label')
@is_logged_in
def label():
    return render_template('label.html')


if __name__ == "__main__":
    app.secret_key = 'secret123'
    app.run(debug=True)
