from flask import Flask, render_template, redirect, g, request, session, url_for, jsonify, flash
import secrets
import hashlib
import random
from werkzeug.utils import secure_filename
import os
import sqlite3

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
DATABASE = 'database.db'

def hash_password(password):
    hash_object = hashlib.sha256()
    hash_object.update(password.encode('utf-8'))
    return hash_object.hexdigest()
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.route('/', methods=["GET", "POST"])
def sign_in():
    session.clear()
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        db = get_db()
        cur = db.execute('SELECT * FROM User_Data WHERE user_login = ?', (username,))
        entries = cur.fetchall()
        if len(entries) == 0:
            flash('Invalid username or password', 'error')
            return render_template("sign_in.html")
        else:
            if hash_password(password) == entries[0][3]:
                session['username'] = username
                session['id_user'] = entries[0][0]
                session["main"] = 0
                session["language"] = entries[0][5]
            else:
                flash('Invalid username or password', 'error')
                render_template("sign_in.html")
        return redirect("/homepage")
    elif request.method == "GET":
        return render_template("sign_in.html")

@app.route('/sign_up', methods=["GET", "POST"])
def sign_up():
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if not name:
            return redirect("/sign_up")
        elif not username:
            return redirect("/sign_up")
        elif not password:
            return redirect("/sign_up")
        elif not confirm_password:
            return redirect("/sign_up")

        if confirm_password != password:
            return redirect("/sign_up")


        db = get_db()
        cur = db.execute('SELECT * FROM User_Data WHERE user_login = ?', (username,))
        entries = cur.fetchall()
        if len(entries) > 0:
            return redirect("/sign_up")

        db.execute('INSERT INTO User_Data (user_login, name, hash_password) VALUES (?,?,?)', (username, name, hash_password(password), ))
        db.commit()
        cur = db.execute('SELECT * FROM User_Data WHERE user_login = ?', (username,))
        entries = cur.fetchall()
        session['username'] = username
        session['id_user'] = entries[0][0]
        session["main"] = 0
        session["language"] = entries[0][5]
        return redirect("/homepage")

    elif request.method == "GET":
        return render_template("sign_up.html")

UPLOAD_FOLDER = 'static/users_avatars'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/homepage', methods=["GET", "POST"])
def homepage():
    if 'username' in session:
        db = get_db()
        cur = db.execute('SELECT * FROM User_Data WHERE id_user = ?',
                         (session['id_user'],))
        entries = cur.fetchall()
        session["avatar"] = entries[0][4].replace('_', '.')
        session["login"] = entries[0][1]
        count_words = len(db.execute("""SELECT * FROM Words
                                JOIN Sets ON Words.id_set = Sets.id_set
                                WHERE Sets.id_user = ?""",
                                     (session["id_user"],)).fetchall())
        count_sets = len(db.execute("SELECT * FROM Sets WHERE id_user = ?",
                                    (session["id_user"],)).fetchall())
        if request.method == 'POST':

            for i in range(7):
                if f'return' in request.form:
                    session["main"] = 0
                    return redirect("/homepage")
                if f'return-back' in request.form:
                    session["main"] = 4
                    return redirect("/homepage")
                elif f'main-{i}' in request.form:
                    session["main"] = i
                    return redirect("/homepage")
                elif f'exit' in request.form:
                    return redirect("/")
                elif f'change-language' in request.form:
                    if (session["language"] == 1):
                        session["language"] += 1
                        db.execute('UPDATE User_Data SET language = ? WHERE id_user = ?',
                                   (session["language"], session["id_user"],))
                        db.commit()
                    elif (session["language"] == 2):
                        session["language"] -= 1
                        db.execute('UPDATE User_Data SET language = ? WHERE id_user = ?',
                                   (session["language"], session["id_user"],))
                        db.commit()
                    return redirect("/homepage")
                elif f'change-login' in request.form:
                    session["main"] = "change-login"
                    cur = db.execute("SELECT * FROM User_Data WHERE id_user = ?",
                                     (session['id_user'],))
                    entries = cur.fetchall()
                    return redirect("/homepage")
                elif f'change-name' in request.form:
                    session["main"] = "change-name"
                    return redirect("/homepage")
                elif f'change-avatar' in request.form:
                    session["main"] = "change-avatar"
                    return redirect("/homepage")
                elif f'change-password' in request.form:
                    session["main"] = "change-password"
                    return redirect("/homepage")
                elif f'save-new-login' in request.form:
                    new_login = request.form.get("new-login")
                    if len(db.execute("SELECT * FROM User_Data WHERE user_login = ?",
                                      (new_login,)).fetchall()) == 0:
                        db.execute('UPDATE User_Data SET user_login = ? WHERE id_user = ?',
                                   (new_login,
                                    session['id_user'],))
                        db.commit()
                    return redirect("/homepage")
                elif f'save-new-name' in request.form:
                    new_name = request.form.get("new-name")
                    db.execute('UPDATE User_Data SET name = ? WHERE id_user = ?',
                               (new_name,
                                session['id_user'],))
                    db.commit()
                    return redirect("/homepage")
                elif f'save-new-avatar' in request.form:
                    if 'file' not in request.files:
                        print(1)
                        return redirect("/homepage")
                    file = request.files['file']
                    if file.filename == '':
                        print(2)
                        return redirect("/homepage")
                    if file and allowed_file(file.filename):
                        filename = secure_filename(str(session["id_user"])+".png")
                        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                        session["avatar"] = filename
                        db.execute("UPDATE User_Data SET avatar = ? WHERE id_user = ?",
                                   (filename.replace('.', '_'),
                                    session['id_user'],))
                        db.commit()
                        print(3)
                        return redirect("/homepage")
                    print(4)
                    return redirect("/homepage")
                elif f'save-new-password' in request.form:
                    old_password = request.form.get("old-password")
                    new_password = request.form.get("new-password")
                    repeat_new_password = request.form.get("repeat-new-password")
                    if new_password != repeat_new_password:
                        return redirect("/homepage")
                    server_old_password = db.execute("SELECT * FROM User_Data WHERE id_user = ?",
                                                     (str(session['id_user']),)).fetchone()[3]
                    if hash_password(old_password) != server_old_password:
                        return redirect("/homepage")
                    db.execute('UPDATE User_Data SET hash_password = ? WHERE id_user = ?',
                               (hash_password(new_password),
                                session['id_user'],))
                    db.commit()
                    return redirect("/homepage")

        else:
            session['translate'] = db.execute("SELECT * FROM Application_Text").fetchall()
            return render_template("homepage.html",
                                   username=entries[0][2],
                                   main=session["main"],
                                   avatar=session["avatar"],
                                   language=session['translate'],
                                   language_id=session["language"],
                                   login=session["login"],
                                   count_words=count_words,
                                   count_sets=count_sets)
    else:
        return redirect("/")

@app.route('/edit-sets', methods=["GET", "POST"])
def editsets():
    if 'username' in session:
        db = get_db()
        cur = db.execute('SELECT * FROM Sets WHERE id_user = ?',
                         (session['id_user'],))
        entries = cur.fetchall()
        if request.method == 'POST':
            if f'add' in request.form:
                button_pressed = f'Button {1} was pressed!'
                return redirect("/add_set")
            else:
                for i in range(len(entries)):
                    if f'remove-button-{i}' in request.form:
                        cur = db.execute('SELECT * FROM Sets WHERE id_user = ?',
                                         (session['id_user'],)).fetchall()
                        db.execute('DELETE FROM Sets WHERE id_set = ?',
                                   (cur[i][0],))
                        db.execute('DELETE FROM Words WHERE id_set = ?',
                                   (cur[i][0],))
                        db.commit()
                        return redirect("/edit-sets")

                    elif f'edit-button-{i}' in request.form:
                        cur = db.execute('SELECT * FROM Sets WHERE id_user = ?', (session['id_user'],)).fetchall()
                        words = db.execute('SELECT * FROM Words WHERE id_set = ?', (cur[i][0],)).fetchall()
                        session["edit_current_set"] = db.execute('SELECT * FROM Sets WHERE id_user = ?', (session['id_user'],)).fetchall()[i]
                        session["words"] = words
                        return redirect('edit-set')
                return render_template("edit_sets.html",
                                       sets=entries,
                                       language=session['translate'],
                                       language_id=session["language"])
        elif request.method == 'GET':
            return render_template("edit_sets.html",
                                   sets=entries, language=session['translate'],
                                   language_id=session["language"])
    else:
        return redirect("/")

@app.route('/choose_set', methods=["GET", "POST"])
def choose_set():
    if 'username' in session:
        db = get_db()
        cur = db.execute('SELECT * FROM Sets WHERE id_user = ?', (session['id_user'],))
        entries = cur.fetchall()
        if request.method == 'POST':
                for i in range(len(entries)):
                    if f'remove-button-{i}' in request.form:
                        words = db.execute('SELECT * FROM Words WHERE id_set = ?',
                                           (entries[i][0],)).fetchall()
                        random.shuffle(words)
                        session["training-set"] = words
                        return redirect("/training")
                return redirect("/")
        elif request.method == 'GET':
            return render_template("choose_set.html",
                                   sets=entries,
                                   language=session['translate'],
                                   language_id=session["language"])
    else:
        return redirect("/")

current_word_index = 0
error_count = 0


@app.route('/training')
def training():
    session['translations'] = {
        28: {"en": "Check", "uk": "Перевірити"},
        29: {"en": "Check results", "uk": "Перевірити результати"},
        30: {"en": "Continue", "uk": "Продовжити"}
    }

    global current_word_index, error_count
    current_word_index = 0
    error_count = 0
    word = session["training-set"][current_word_index][2]
    translation = session["training-set"][current_word_index][3]

    language = session.get("language", "en")
    translations = session.get('translations', {})

    check_text = translations.get(28, {}).get(language, "Check")
    continue_text = translations.get(30, {}).get(language, "Continue")
    check_results_text = translations.get(29, {}).get(language, "Check results")

    return render_template('training.html',
                           word=word,
                           translation=translation,
                           error_count=error_count,
                           game_over=False,
                           total_words=len(session["training-set"]),
                           check_text=check_text,
                           continue_text=continue_text,
                           check_results_text=check_results_text,
                           language=session['translate'],
                           language_id=session["language"])


@app.route('/check', methods=['POST'])
def check():
    global current_word_index, error_count
    user_input = request.form['user_input']
    correct_translation = request.form['correct_translation']

    if user_input != correct_translation:
        error_count += 1

    current_word_index += 1
    if current_word_index >= len(session["training-set"]):
        return jsonify({"game_over": True, "error_count": error_count})

    next_word = session["training-set"][current_word_index][2]
    next_translation = session["training-set"][current_word_index][3]
    return jsonify({"next_word": next_word, "next_translation": next_translation, "error_count": error_count, "game_over": False})

@app.route('/results')
def results():
    global error_count
    return render_template('results.html', error_count=error_count)

@app.errorhandler(404)
def page_not_found(e):
    return "404"

@app.route('/add_set', methods=["GET", "POST"])
def add_set():
    if 'username' in session:
        if request.method == 'POST':
            title = request.form.get("title")
            description = request.form.get("description")
            word = request.form.get("word")
            translate = request.form.get("translate")

            if not title:
                return redirect("/add_set")
            elif not description:
                return redirect("/add_set")
            elif not word:
                return redirect("/add_set")
            elif not translate:
                return redirect("/add_set")
            db = get_db()
            db.execute("INSERT INTO Sets (id_user, title, description) VALUES (?,?,?)",
                       (session['id_user'], title, description,))
            db.commit()
            cur = db.execute("SELECT * FROM Sets WHERE id_user = ?",
                             (session['id_user'],))
            entries = cur.fetchall()
            res = entries[len(entries) - 1]
            db.execute("INSERT INTO Words (id_set, word, translate) VALUES (?,?,?)",
                       (res[0], word, translate,))
            db.commit()
            return redirect("/edit-sets")

        else:
            return render_template("add_set.html")
    else:
        return redirect("/")

@app.route('/edit-set', methods=["GET", "POST"])
def editset():
    if 'username' in session:
        if request.method == 'POST':
            for i in range(len(session["words"])+1):
                if f'remove-button-{i}' in request.form:
                    db = get_db()
                    cur = db.execute('SELECT * FROM Words WHERE id_set = ?',
                                     (session["edit_current_set"][0],)).fetchall()
                    db.execute('DELETE FROM Words WHERE id_word = ?',
                               (cur[i][0],))
                    words = db.execute('SELECT * FROM Words WHERE id_set = ?',
                                       (session["edit_current_set"][0],)).fetchall()
                    session["words"] = words
                    db.commit()
                    return redirect("/edit-set")
                elif f'save' in request.form:
                    db = get_db()
                    db.execute('UPDATE Sets SET title = ?, description = ? WHERE id_set = ?',
                                     (request.form.get("title"),
                                      request.form.get("description"),
                                      session["edit_current_set"][0],))
                    session["edit_current_set"] = db.execute('SELECT * FROM Sets WHERE id_user = ?',
                                                             (session['id_user'],)).fetchall()[i]
                    db.commit()
                    return redirect("/edit-sets")
                elif f'edit-button-{i}' in request.form:
                    return render_template("edit_set.html",
                                           id_word=i,
                                           words=session["words"],
                                           set=session["edit_current_set"],
                                           add_new=False,
                                           language=session['translate'],
                                           language_id=session["language"])
                elif f'add-button' in request.form:
                    return render_template("edit_set.html",
                                           id_word=-1,
                                           words=session["words"],
                                           set=session["edit_current_set"],
                                           add_new=True,
                                           language=session['translate'],
                                           language_id=session["language"])

                elif f'add-word' in request.form:
                    word = request.form.get("word")
                    translate = request.form.get("translate")
                    db = get_db()
                    db.execute("INSERT INTO Words (id_set, word, translate) VALUES (?,?,?)", (session["edit_current_set"][0], word, translate,))
                    db.commit()
                    words = db.execute('SELECT * FROM Words WHERE id_set = ?',
                                       (session["edit_current_set"][0],)).fetchall()
                    session["words"] = words
                    db.commit()
                    return redirect("edit-set")
                elif f'save-word-{i}' in request.form:
                    db = get_db()
                    db.execute('UPDATE Words SET word = ?, translate = ? WHERE id_word = ?',
                               (request.form.get("new-word"),
                                request.form.get("new-translate"),
                                session["words"][i][0],))
                    db.commit()
                    session["words"] = db.execute('SELECT * FROM Words WHERE id_set = ?',
                                                  (session["edit_current_set"][0],)).fetchall()
                    return redirect("edit-set")
            return redirect("/edit-set")
        else:
            return render_template("edit_set.html",
                                   words=session["words"],
                                   set=session["edit_current_set"],
                                   add_new=False,
                                   language=session['translate'],
                                   language_id=session["language"])
    else:
        return redirect("/")


if __name__ == '__main__':
    app.run(debug=True)

