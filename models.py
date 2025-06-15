from app import db
from flask_login import UserMixin
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

# Association table for many-to-many relationship between users and family groups
group_members = db.Table('group_members',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('family_group_id', db.Integer, db.ForeignKey('family_group.id'), primary_key=True),
    db.Column('joined_at', db.DateTime, default=datetime.utcnow)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    total_points = db.Column(db.Integer, default=0)
    reading_streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    last_read_date = db.Column(db.Date)
    monthly_goal = db.Column(db.Integer, default=2)  # Books per month
    
    # Relationships
    books = db.relationship('Book', backref='reader', lazy=True, cascade='all, delete-orphan')
    created_groups = db.relationship('FamilyGroup', backref='creator', lazy=True)
    family_groups = db.relationship('FamilyGroup', secondary=group_members, 
                                  back_populates='members', lazy='dynamic')
    # Will add achievements later after Achievement model is defined
    
    def set_password(self, password):
        """Hash and set the user's password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches the hash"""
        return check_password_hash(self.password_hash, password)
    
    def get_group_points(self, group_id):
        """Get user's points within a specific family group"""
        group_books = Book.query.filter_by(user_id=self.id, status='Read').join(
            group_members, group_members.c.user_id == self.id
        ).filter(group_members.c.family_group_id == group_id).all()
        return sum(book.points for book in group_books)
    
    def update_reading_streak(self, book_completion_date):
        """Update reading streak when a book is completed"""
        today = book_completion_date.date() if isinstance(book_completion_date, datetime) else book_completion_date
        
        if self.last_read_date:
            days_diff = (today - self.last_read_date).days
            if days_diff == 1:
                # Consecutive day - extend streak
                self.reading_streak += 1
            elif days_diff == 0:
                # Same day - no change to streak
                pass
            else:
                # Gap in reading - reset streak
                self.reading_streak = 1
        else:
            # First book completion
            self.reading_streak = 1
        
        # Update longest streak if current streak is longer
        if self.reading_streak > self.longest_streak:
            self.longest_streak = self.reading_streak
        
        self.last_read_date = today
    
    def get_monthly_progress(self):
        """Get current month's reading progress"""
        now = datetime.utcnow()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        books_this_month = Book.query.filter(
            Book.user_id == self.id,
            Book.status == 'Read',
            Book.date_completed >= start_of_month
        ).count()
        
        return {
            'books_read': books_this_month,
            'goal': self.monthly_goal,
            'percentage': int((books_this_month / self.monthly_goal) * 100) if self.monthly_goal > 0 else 0
        }
    
    def get_reading_stats(self):
        """Get comprehensive reading statistics"""
        total_books = Book.query.filter_by(user_id=self.id, status='Read').count()
        total_pages = db.session.query(db.func.sum(Book.page_count)).filter(
            Book.user_id == self.id, Book.status == 'Read'
        ).scalar() or 0
        
        # Books read this year
        year_start = datetime.utcnow().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        books_this_year = Book.query.filter(
            Book.user_id == self.id,
            Book.status == 'Read',
            Book.date_completed >= year_start
        ).count()
        
        return {
            'total_books': total_books,
            'total_pages': total_pages,
            'books_this_year': books_this_year,
            'current_streak': self.reading_streak,
            'longest_streak': self.longest_streak,
            'monthly_progress': self.get_monthly_progress()
        }
    
    def check_achievements(self):
        """Check and award new achievements - simplified version"""
        # For now, return empty list - will implement achievements later
        return []
    
    def __repr__(self):
        return f'<User {self.username}>'

class FamilyGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    invite_code = db.Column(db.String(10), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    max_members = db.Column(db.Integer, default=15)
    
    # Relationships
    members = db.relationship('User', secondary=group_members, 
                            back_populates='family_groups', lazy='dynamic')
    
    def generate_invite_code(self):
        """Generate a unique invite code for the group"""
        import string
        import random
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not FamilyGroup.query.filter_by(invite_code=code).first():
                self.invite_code = code
                break
    
    def get_leaderboard(self):
        """Get sorted leaderboard for this group"""
        leaderboard = []
        members_list = list(self.members)
        for member in members_list:
            read_books = Book.query.filter_by(user_id=member.id, status='Read').all()
            total_points = sum(book.points for book in read_books)
            total_books = len(read_books)
            leaderboard.append({
                'user': member,
                'points': total_points,
                'books_read': total_books,
                'streak': member.reading_streak
            })
        return sorted(leaderboard, key=lambda x: x['points'], reverse=True)
    
    def get_group_stats(self):
        """Get group reading statistics"""
        total_books = 0
        total_pages = 0
        total_points = 0
        
        members_list = list(self.members)
        for member in members_list:
            member_books = Book.query.filter_by(user_id=member.id, status='Read').all()
            total_books += len(member_books)
            total_pages += sum(book.page_count for book in member_books)
            total_points += sum(book.points for book in member_books)
        
        return {
            'total_books': total_books,
            'total_pages': total_pages,
            'total_points': total_points,
            'member_count': self.members.count()
        }
    
    def __repr__(self):
        return f'<FamilyGroup {self.name}>'

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    page_count = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='To Read')  # 'To Read', 'Reading', 'Read'
    points = db.Column(db.Integer, default=0)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    date_completed = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __init__(self, **kwargs):
        super(Book, self).__init__(**kwargs)
    
    def calculate_points(self):
        """Calculate points based on page count"""
        if self.status == 'Read':
            # Award 1 point per 10 pages, minimum 5 points
            self.points = max(5, self.page_count // 10)
        else:
            self.points = 0
    
    def mark_as_read(self):
        """Mark book as read and calculate points"""
        self.status = 'Read'
        self.date_completed = datetime.utcnow()
        self.calculate_points()
        
        # Update user's total points and streak
        user = User.query.get(self.user_id)
        if user:
            user.total_points = sum(book.points for book in user.books if book.status == 'Read')
            user.update_reading_streak(self.date_completed)
            
            return True
        return False
    
    def get_reading_time_estimate(self):
        """Estimate reading time based on page count (assuming 250 words/page, 200 words/minute)"""
        words = self.page_count * 250
        minutes = words / 200
        hours = int(minutes // 60)
        mins = int(minutes % 60)
        return f"{hours}h {mins}m" if hours > 0 else f"{mins}m"
    
    def __repr__(self):
        return f'<Book {self.title} by {self.author}>'