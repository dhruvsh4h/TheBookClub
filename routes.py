from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, FamilyGroup, Book
from forms import LoginForm, RegistrationForm, CreateGroupForm, JoinGroupForm, AddBookForm

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
    
    # Get user's family groups
    family_groups = current_user.family_groups.all()
    
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
                         family_groups=family_groups,
                         stats=stats)

@app.route('/family-groups')
@login_required
def family_groups():
    """Display user's family groups"""
    user_groups = current_user.family_groups.all()
    return render_template('family_groups.html', groups=user_groups)

@app.route('/create-group', methods=['GET', 'POST'])
@login_required
def create_group():
    """Create a new family group"""
    form = CreateGroupForm()
    if form.validate_on_submit():
        # Use the correct FamilyGroup model
        new_group = FamilyGroup(
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
    """Join a family group using invite code"""
    form = JoinGroupForm()
    if form.validate_on_submit():
        try:
            # --- THIS IS THE CORRECTED LINE ---
            group = FamilyGroup.query.filter_by(invite_code=form.invite_code.data).first()

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
    """Display family group details and leaderboard"""
    group = FamilyGroup.query.get_or_404(group_id)
    
    # Check if user is a member
    if current_user not in group.members:
        flash('You are not a member of this group.', 'error')
        return redirect(url_for('family_groups'))
    
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

@app.route('/add-book', methods=['GET', 'POST'])
@login_required
def add_book():
    """Add a new book"""
    form = AddBookForm()
    if form.validate_on_submit():
        try:
            book = Book(
                title=form.title.data,
                author=form.author.data,
                page_count=form.page_count.data,
                status=form.status.data,
                user_id=current_user.id
            )
            
            # Calculate points if book is marked as read
            if book.status == 'Read':
                book.mark_as_read()
            
            db.session.add(book)
            db.session.commit()
            
            # Update user's total points
            current_user.total_points = sum(b.points for b in current_user.books if b.status == 'Read')
            db.session.commit()
            
            flash(f'Book "{book.title}" added successfully!', 'success')
            return redirect(url_for('books'))
        except Exception:
            db.session.rollback()
            flash('Error adding book. Please try again.', 'error')
    
    return render_template('add_book.html', form=form)

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
