from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, Group, Book, Feedback, UserBook
from forms import LoginForm, RegistrationForm, CreateGroupForm, JoinGroupForm, AddBookForm, BookSearchForm
import requests

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Logged in successfully!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'error')
    
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    # Get user's recent books
    recent_books = Book.query.filter_by(user_id=current_user.id).order_by(Book.date_added.desc()).limit(5).all()
    
    # Get user's  groups
    groups = current_user.groups.all()
    
    # Calculate enhanced reading stats
    total_books = Book.query.filter_by(user_id=current_user.id).count()
    books_read = Book.query.filter_by(user_id=current_user.id, status='Read').count()
    books_reading = Book.query.filter_by(user_id=current_user.id, status='Reading').count()
    
    # Get enhanced statistics
    reading_stats = current_user.get_reading_stats()
    monthly_progress = current_user.get_monthly_progress()
    
    stats = {
        'total_books': total_books,
        'books_read': books_read,
        'books_reading': books_reading,
        'total_points': current_user.total_points,
        'current_streak': current_user.reading_streak,
        'longest_streak': current_user.longest_streak,
        'total_pages': reading_stats['total_pages'],
        'books_this_year': reading_stats['books_this_year'],
        'monthly_progress': monthly_progress
    }
    
    return render_template('dashboard.html', 
                         recent_books=recent_books, 
                         groups=groups,
                         stats=stats)

@app.route('/groups')
@login_required
def groups():
    """Display user's groups"""
    user_groups = current_user.groups.all()
    return render_template('groups.html', groups=user_groups)

@app.route('/create-group', methods=['GET', 'POST'])
@login_required
def create_group():
    """Create a new group"""
    form = CreateGroupForm()
    if form.validate_on_submit():
        # Use the correct Group model
        new_group = Group(
            name=form.name.data,
            description=form.description.data,
            max_members=form.max_members.data,
            creator_id=current_user.id  # Set the creator
        )

        # Generate the invite code
        new_group.generate_invite_code()

        # Add the current user as the first member
        new_group.members.append(current_user)

        db.session.add(new_group)
        db.session.commit()

        flash(f'Group "{new_group.name}" created successfully!', 'success')

        # Redirect to the correct 'group_detail' endpoint
        return redirect(url_for('group_detail', group_id=new_group.id)) 

    return render_template('create_group.html', title='Create Group', form=form)

@app.route('/join-group', methods=['GET', 'POST'])
@login_required
def join_group():
    """Join a group using invite code"""
    form = JoinGroupForm()
    if form.validate_on_submit():
        try:
            # --- THIS IS THE CORRECTED LINE ---
            group = Group.query.filter_by(invite_code=form.invite_code.data).first()

            if not group:
                flash('Invalid invite code.', 'error')
            elif current_user in group.members:
                flash('You are already a member of this group.', 'info')
            elif group.members.count() >= group.max_members:
                flash('This group is full.', 'error')
            else:
                group.members.append(current_user)
                db.session.commit()
                flash(f'Successfully joined "{group.name}"!', 'success')
                return redirect(url_for('group_detail', group_id=group.id))
        except Exception:
            db.session.rollback()
            flash('Error joining group. Please try again.', 'error')

    return render_template('join_group.html', form=form)

@app.route('/group/<int:group_id>')
@login_required
def group_detail(group_id):
    """Display group details and leaderboard"""
    group = Group.query.get_or_404(group_id)
    
    # Check if user is a member
    if current_user not in group.members:
        flash('You are not a member of this group.', 'error')
        return redirect(url_for('groups'))
    
    # Get leaderboard
    leaderboard = group.get_leaderboard()
    
    # Get recent group activity (recent books read by members)
    recent_activity = Book.query.filter(
        Book.user_id.in_([member.id for member in group.members]),
        Book.status == 'Read'
    ).order_by(Book.date_completed.desc()).limit(10).all()
    
    return render_template('group_detail.html', 
                         group=group, 
                         leaderboard=leaderboard,
                         recent_activity=recent_activity)

@app.route('/books')
@login_required
def books():
    """Display user's books"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    
    query = Book.query.filter_by(user_id=current_user.id)
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    books = query.order_by(Book.date_added.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('books.html', books=books, status_filter=status_filter)
# Removed this route to avoid confusion with the new search functionality
# Uncomment if you want to keep the add book functionality
# from forms import AddBookForm
# @app.route('/add-book', methods=['GET', 'POST'])
# @login_required
# def add_book():
#     """Add a new book"""
#     form = AddBookForm()
#     if form.validate_on_submit():
#         try:
#             book = Book(
#                 title=form.title.data,
#                 author=form.author.data,
#                 page_count=form.page_count.data,
#                 status=form.status.data,
#                 user_id=current_user.id
#             )
            
#             # Calculate points if book is marked as read
#             if book.status == 'Read':
#                 book.mark_as_read()
            
#             db.session.add(book)
#             db.session.commit()
            
#             # Update user's total points
#             current_user.total_points = sum(b.points for b in current_user.books if b.status == 'Read')
#             db.session.commit()
            
#             flash(f'Book "{book.title}" added successfully!', 'success')
#             return redirect(url_for('books'))
#         except Exception:
#             db.session.rollback()
#             flash('Error adding book. Please try again.', 'error')
    
#     return render_template('add_book.html', form=form)

@app.route('/mark-read/<int:book_id>')
@login_required
def mark_book_read(book_id):
    """Mark a book as read"""
    book = Book.query.get_or_404(book_id)
    
    # Check if book belongs to current user
    if book.user_id != current_user.id:
        flash('You can only modify your own books.', 'error')
        return redirect(url_for('books'))
    
    try:
        book.mark_as_read()
        db.session.commit()
        
        # Update user's total points
        current_user.total_points = sum(b.points for b in current_user.books if b.status == 'Read')
        db.session.commit()
        
        flash(f'Congratulations! You earned {book.points} points for reading "{book.title}"!', 'success')
    except Exception:
        db.session.rollback()
        flash('Error updating book status.', 'error')
    
    return redirect(url_for('books'))

@app.route('/delete-book/<int:book_id>')
@login_required
def delete_book(book_id):
    """Delete a book"""
    book = Book.query.get_or_404(book_id)
    
    # Check if book belongs to current user
    if book.user_id != current_user.id:
        flash('You can only delete your own books.', 'error')
        return redirect(url_for('books'))
    
    try:
        db.session.delete(book)
        db.session.commit()
        
        # Update user's total points
        current_user.total_points = sum(b.points for b in current_user.books if b.status == 'Read')
        db.session.commit()
        
        flash(f'Book "{book.title}" deleted successfully.', 'info')
    except Exception:
        db.session.rollback()
        flash('Error deleting book.', 'error')
    
    return redirect(url_for('books'))

@app.route('/settings', methods=['GET'])
@login_required
def settings():
    """User settings page"""
    reading_stats = current_user.get_reading_stats()
    return render_template('settings.html', stats=reading_stats)

@app.route('/update-settings', methods=['POST'])
@login_required
def update_settings():
    """Update user settings"""
    try:
        monthly_goal = request.form.get('monthly_goal', type=int)
        if monthly_goal and 1 <= monthly_goal <= 20:
            current_user.monthly_goal = monthly_goal
            db.session.commit()
            flash(f'Monthly goal updated to {monthly_goal} books!', 'success')
        else:
            flash('Please enter a valid monthly goal (1-20 books).', 'error')
    except Exception as e:
        db.session.rollback()
        flash('Error updating settings. Please try again.', 'error')
    
    return redirect(url_for('settings'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
@app.route('/search-book', methods=['GET', 'POST'])
@login_required
def search_book():
    form = BookSearchForm()
    search_results = []

    if form.validate_on_submit():
        query = form.query.data
        api_key = app.config['GOOGLE_BOOKS_API_KEY']
        url = f"https://www.googleapis.com/books/v1/volumes?q={query}&key={api_key}"

        try:
            response = requests.get(url)
            response.raise_for_status()  # Will raise an error for bad responses
            data = response.json()

            # Process the results from the API
            if 'items' in data:
                for item in data['items']:
                    volume_info = item.get('volumeInfo', {})
                    book_data = {
                        'google_id': item.get('id'),
                        'title': volume_info.get('title', 'No Title'),
                        'author': ', '.join(volume_info.get('authors', ['Unknown'])),
                        'page_count': volume_info.get('pageCount', 0),
                        'cover_url': volume_info.get('imageLinks', {}).get('thumbnail')
                    }
                    if book_data['page_count'] > 0:
                        search_results.append(book_data)
        except requests.exceptions.RequestException as e:
            flash(f"Error calling Google Books API: {e}", 'danger')

    return render_template('search_book.html', form=form, results=search_results)

@app.route('/add-book-from-api', methods=['POST'])
@login_required
def add_book_from_api():
    try:
        # Get book details from the submitted form
        title = request.form.get('title')
        author = request.form.get('author')
        page_count = int(request.form.get('page_count', 0))

        # Check if the book already exists for this user
        book = Book.query.filter_by(
            title=title,
            author=author,
            page_count=page_count,
            user_id=current_user.id
        ).first()

        if not book:
            # Create the book and add it to the database
            book = Book(
                title=title,
                author=author,
                page_count=page_count,
                user_id=current_user.id
            )
            db.session.add(book)
            db.session.commit()

        # Optionally, you can also create a UserBook entry if you use that model for tracking
        # For now, just flash success
        flash(f'"{title}" has been added to your reading list!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding book: {e}', 'danger')

    return redirect(url_for('search_book'))

@app.route('/feedback', methods=['GET', 'POST'])
def feedback_page():
    if request.method == 'POST':
        username = request.form.get('username', '')
        rating = request.form.get('rating', '')
        feedback_text = request.form.get('feedback', '')
        feedback = Feedback(
            username=username,
            rating=int(rating) if rating else None,
            feedback=feedback_text
        )
        db.session.add(feedback)
        db.session.commit()
        return render_template('feedback.html', message="Thank you for your feedback!")
    return render_template('feedback.html')