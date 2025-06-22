from flask import Blueprint, render_template, request, redirect, url_for, flash
from . import db  # Assuming you have a db object from Flask SQLAlchemy
from .models import Feedback  # Assuming you have a Feedback model

bp = Blueprint('feedback', __name__)

@bp.route('/feedback', methods=['GET', 'POST'])
def feedback_page():
    if request.method == 'POST':
        name = request.form.get('name')
        rating = request.form.get('rating')
        feedback_text = request.form.get('feedback')

        # Basic validation
        if not name or not rating or not feedback_text:
            flash('All fields are required.', 'danger')
            return redirect(url_for('feedback.feedback_page'))

        # Save to database
        feedback = Feedback(name=name, rating=int(rating), feedback=feedback_text)
        db.session.add(feedback)
        db.session.commit()
        flash('Thank you for your feedback!', 'success')
        return redirect(url_for('feedback.feedback_page'))

    return render_template('feedback.html')