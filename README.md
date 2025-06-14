# BookQuest Tracker 📚✨

A social and gamified web app to make reading a shared adventure with friends and family.

## ✨ Core Features

* **Social Groups & Leaderboards:** Create private groups, invite members, and compete on a leaderboard.
* **Gamified Reading:** Earn points for finishing books, with more points awarded for longer books.
* **Personal Tracking:** Search for books via the Google Books API and manage your personal reading list.
* **Secure Accounts:** Standard user registration and login.

## 🛠️ Tech Stack

* **Backend:** Python / Flask
* **Database:** SQLite / Flask-SQLAlchemy
* **Frontend:** HTML, CSS, JS, Bootstrap 5
* **API:** Google Books API

## 🚀 Quickstart

1.  **Clone the repo**
    ```sh
    git clone [https://github.com/dhruvsh4h/TheBookClub.git](https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git)
    cd TheBookClub
    ```

2.  **Setup Environment & Install Dependencies**
    ```sh
    python -m venv venv
    # Activate venv (see original README for OS-specific command)
    pip install -r requirements.txt
    ```

3.  **Initialize DB & Run**
    ```sh
    flask shell
    # >>> from main import db, create_app; app = create_app();
    # >>> with app.app_context(): db.create_all()
    # >>> exit()
    flask run
    ```
    Access at `http://127.0.0.1:5000`.

## 📈 Roadmap

*  User profiles and reading stats
*  Book reviews and ratings
*  Monthly leaderboards and group goals
*  "Currently Reading" status

## 📄 License

Distributed under the MIT License.
