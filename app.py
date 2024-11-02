from flask import Flask, send_from_directory, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from datetime import datetime

app = Flask(__name__, static_folder='frontend/build')

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:Harshith**24@localhost/library_management'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    available = db.Column(db.Integer, default=0)  # Change to Integer with default 0
    aisle = db.Column(db.String(50), nullable=False)
    #borrowed_books = db.relationship('BorrowedBook', back_populates='user')

class User(db.Model):
    __tablename__ = 'users'
    #id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), primary_key=True, unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(10), nullable=False)
    #borrowed_books = db.relationship('BorrowedBook', back_populates='book')

class BorrowedBook(db.Model):
    __tablename__ = 'borrowed_books'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('users.user_id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    book_title = db.Column(db.String(50), nullable=False)
    borrow_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date, nullable=True)

    # Relationships to User and Book tables
    #user = db.relationship('User', back_populates='borrowed_books')
    #book = db.relationship('Book', back_populates='borrowed_books')

@app.route('/')
def main_page():
    return 'Home page'

@app.route('/home', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        
        if form_type == 'login':
            user_id = request.form.get('login_user_id')
            password = request.form.get('login_password')
            user = User.query.filter_by(user_id=user_id).first()

            if user and user.password == password:
                if user.type == 'Librarian':
                    return jsonify({
                        'success': True,
                        'message': 'Login successful! Redirecting to library...',
                        'redirect_url': url_for('library')
                    })
                else:
                    # Append user_id as a query parameter
                    return jsonify({
                        'success': True,
                        'message': 'Login successful! Redirecting to user page...',
                        'redirect_url': url_for('user', user_id=user_id)
                    })
            else:
                return jsonify({'success': False, 'message': 'Invalid login credentials. Please try again.'})

        elif form_type == 'register':
            # Registration form processing
            user_id = request.form.get('register_user_id')
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            age = request.form.get('age')
            password = request.form.get('register_password')
            user_type = request.form.get('user_type')

            # Check if the user ID already exists
            if User.query.filter_by(user_id=user_id).first():
                return jsonify({'success': False, 'message': 'User ID already exists! Please choose a different one.'})

            # Create a new user
            new_user = User(user_id=user_id, first_name=first_name, last_name=last_name, age=age, password=password, type=user_type)
            db.session.add(new_user)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Registration successful! Please log in.'})

    return render_template('home.html')

@app.route('/library')
def library():
    # user = User.query.filter_by(user_id=user_id).first()
    # if not user:
    #     return redirect(url_for('home'))
    return send_from_directory(app.static_folder, 'library.html')
    # return render_template('library.html', user=user)

@app.route('/user/<user_id>')
def user(user_id):
    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        return redirect(url_for('home'))  # Redirect if user is not found

    return render_template('user.html', user=user)

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json()
    try:
        new_book = Book(
            id=data['id'],
            title=data['title'],
            author=data['author'],
            category=data['category'],
            available=data['available'],  # Now expects an integer
            aisle=data['aisle']
        )
        db.session.add(new_book)
        db.session.commit()
        return jsonify({'message': 'Book added successfully!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to add book!', 'error': str(e)}), 400

@app.route('/delete_book', methods=['DELETE'])
def delete_book():
    data = request.get_json()
    book_id = data.get('id')
    book = Book.query.get(book_id)
    
    if book:
        db.session.delete(book)
        db.session.commit()
        return jsonify({'message': 'Book deleted successfully!'})
    else:
        return jsonify({'message': 'No such book!'}), 404

@app.route('/edit_book', methods=['PUT'])
def edit_book():
    data = request.get_json()
    book_id = data.get('id')
    book = Book.query.get(book_id)

    if book:
        book.title = data['title']
        book.author = data['author']
        book.category = data['category']
        book.available = data['available']  # Update to new integer value
        book.aisle = data['aisle']
        db.session.commit()
        return jsonify({'message': 'Book updated successfully!'})
    else:
        return jsonify({'message': 'No such book!'}), 404

# Helper function to find a book by ID
def find_book_by_id(book_id):
    return Book.query.get(book_id)

@app.route('/borrow_book/<int:user_id>/<int:book_id>', methods=['POST'])
def borrow_book(user_id, book_id):
    app.logger.info(f'Received request to borrow book. User ID: {user_id}, Book ID: {book_id}')

    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        app.logger.error('User not found.')
        return jsonify({'success': False, 'message': 'User not found.'}), 404

    book = Book.query.filter_by(id=book_id).first()
    if not book:
        app.logger.error('Book not found.')
        return jsonify({'success': False, 'message': 'Book not found.'}), 404

    # Check availability
    if book.available <= 0:
        app.logger.warning('No copies available for borrowing.')
        return jsonify({'success': False, 'message': 'No copies available for borrowing.'}), 400

    # Record this specific borrow instance
    new_borrowed_book = BorrowedBook(user_id=user_id, book_id=book_id, book_title=book.title, borrow_date=datetime.now())
    db.session.add(new_borrowed_book)

    # Reduce the availability of the book by 1
    book.available -= 1
    db.session.commit()  # Commit the transaction to the database

    app.logger.info(f'Book "{book.title}" borrowed successfully by User ID: {user_id}')
    return jsonify({'success': True, 'message': f'Book "{book.title}" borrowed successfully!'})

@app.route('/borrowed_books/<int:user_id>')
def get_borrowed_books(user_id):
    borrowed_books = BorrowedBook.query.filter_by(user_id=user_id).all()
    result = [{'id': book.book_id, 'title': book.book_title, 'borrow_date': book.borrow_date, 'return_date': book.return_date} for book in borrowed_books]
    return jsonify({'borrowed_books': result})

# Route for returning a borrowed book
@app.route('/return_book/<int:user_id>', methods=['POST'])
def return_book(user_id):
    data = request.get_json()
    book_id = data.get('book_id')

    # Fetch the borrowed book entry
    borrowed_book = BorrowedBook.query.filter_by(user_id=user_id, book_id=book_id, return_date=None).first()
    
    if not borrowed_book:
        return jsonify({'success': False, 'message': 'No record of this book being borrowed or it has already been returned.'})

    # Update the return date
    borrowed_book.return_date = datetime.now()

    # Fetch the book entry and increment its availability
    book = Book.query.filter_by(id=book_id).first()
    if book:
        book.available += 1  # Assuming 'available' tracks available copies
        db.session.commit()
        return jsonify({'success': True, 'message': 'Book returned successfully!'})
    else:
        return jsonify({'success': False, 'message': 'Book not found in the library.'})

# Route to fetch all books borrowed by the current user
# @app.route('/borrowed_books')
# def get_borrowed_books():
#     if 'username' not in session:
#         return jsonify({"message": "Please log in to view borrowed books."}), 401

#     user_id = session['username']
#     borrowed_books = BorrowedBook.query.filter_by(user_id=user_id).all()

#     user_borrowed_books = []
#     for borrowed in borrowed_books:
#         book = find_book_by_id(borrowed.book_id)
#         if book:
#             user_borrowed_books.append({
#                 'id': book.id,
#                 'title': book.title,
#                 'author': book.author,
#                 'category': book.category,
#                 'available': book.available,
#                 'aisle': book.aisle,
#                 'borrow_date': borrowed.borrow_date.strftime('%Y-%m-%d'),
#                 'return_date': borrowed.return_date.strftime('%Y-%m-%d') if borrowed.return_date else None
#             })

#     return jsonify({"borrowed_books": user_borrowed_books})

@app.route('/categories')
def get_categories():
    categories = db.session.query(Book.category).distinct().all()
    category_list = [category[0] for category in categories]  # Extract the category names from the tuples
    return {"categories": category_list}

@app.route('/report')
def report():
    category = request.args.get('category')
    author = request.args.get('author')
    book_name = request.args.get('book_name')
    all_books = request.args.get('all') == 'true'
    
    # If fetching all books, use ORM directly
    if all_books:
        books = Book.query.all()
        #result = db.session.execute(text("CALL GetAllBooks()"))
    else:
        # Start with a base query
        query = "SELECT * FROM books WHERE 1=1"
        params = {}

        # Adding filtering conditions dynamically
        if category:
            query += " AND category = :category"
            params['category'] = category
        if author:
            query += " AND author = :author"
            params['author'] = author
        if book_name:
            query += " AND title = :book_name"
            params['book_name'] = book_name
        
        # Execute the prepared statement with parameters
        result = db.session.execute(text(query), params)
        books = result.fetchall()

    # Calculate the total count and availability of the filtered books
    total_count = len(books)
    total_available = sum(book.available for book in books)

    # Format the report data
    report_data = {
        'books': [{'id': book.id, 'title': book.title, 'author': book.author, 
                   'category': book.category, 'available': book.available, 
                   'aisle': book.aisle} for book in books],
        'total_count': total_count,
        'available_count': total_available
    }

    return render_template('report.html', report_data=report_data)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
