from flask import Flask, send_from_directory, request, jsonify, render_template, redirect, url_for, session, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
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
    author = db.Column(db.String(100), nullable=False, index=True)
    category = db.Column(db.String(50), nullable=False, index=True)
    available = db.Column(db.Integer, default=0) 
    aisle = db.Column(db.String(50), nullable=False)

class User(db.Model):
    __tablename__ = 'users'
    #id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), primary_key=True, unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(10), nullable=False)

class BorrowedBook(db.Model):
    __tablename__ = 'borrowed_books'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('users.user_id'), nullable=False, index=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    book_title = db.Column(db.String(50), nullable=False)
    borrow_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date, nullable=True)

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
                    return jsonify({
                        'success': True,
                        'message': 'Login successful! Redirecting to user page...',
                        'redirect_url': url_for('user', user_id=user_id)
                    })
            else:
                return jsonify({'success': False, 'message': 'Invalid login credentials. Please try again.'})

        elif form_type == 'register':
            user_id = request.form.get('register_user_id')
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            age = request.form.get('age')
            password = request.form.get('register_password')
            user_type = request.form.get('user_type')

            if User.query.filter_by(user_id=user_id).first():
                return jsonify({'success': False, 'message': 'User ID already exists! Please choose a different one.'})

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
        return redirect(url_for('home')) 

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
            available=data['available'],
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
        book.available = data['available'] 
        book.aisle = data['aisle']
        db.session.commit()
        return jsonify({'message': 'Book updated successfully!'})
    else:
        return jsonify({'message': 'No such book!'}), 404

def find_book_by_id(book_id):
    return Book.query.get(book_id)

@app.route('/borrow_book/<int:user_id>/<int:book_id>', methods=['POST'])
def borrow_book(user_id, book_id):
    try:
        with db.session.begin_nested(): 
            db.session.execute(text("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;"))

            user = User.query.filter_by(user_id=user_id).first()
            book = Book.query.filter_by(id=book_id).first()

            if not user:
                return jsonify({'success': False, 'message': 'User not found.'}), 404
            if not book:
                return jsonify({'success': False, 'message': 'Book not found.'}), 404
            if book.available <= 0:
                return jsonify({'success': False, 'message': 'No copies available for borrowing.'}), 400
            new_borrowed_book = BorrowedBook(
                user_id=user_id,
                book_id=book_id,
                book_title=book.title,
                borrow_date=datetime.now()
            )
            db.session.add(new_borrowed_book)
            book.available -= 1
        db.session.commit()
        return jsonify({'success': True, 'message': 'Book borrowed successfully!'})
    except IntegrityError as e:
        db.session.rollback()
        app.logger.error(f"IntegrityError: {e}")
        return jsonify({'success': False, 'message': 'Transaction error occurred.'}), 500
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Unexpected error: {e}")
        return jsonify({'success': False, 'message': 'An unexpected error occurred.'}), 500


@app.route('/borrowed_books/<int:user_id>')
def get_borrowed_books(user_id):
    query = text("SELECT book_id, book_title, borrow_date, return_date FROM borrowed_books WHERE user_id = :user_id")
    params = {'user_id': user_id}
    
    result = db.session.execute(query, params)
    borrowed_books = result.fetchall()
    
    result = [{'id': book[0], 'title': book[1], 'borrow_date': book[2], 'return_date': book[3]} for book in borrowed_books]
    
    return jsonify({'borrowed_books': result})

@app.route('/return_book/<int:user_id>', methods=['POST'])
def return_book(user_id):
    data = request.get_json()
    book_id = data.get('book_id')

    borrowed_book = BorrowedBook.query.filter_by(user_id=user_id, book_id=book_id, return_date=None).first()
    
    if not borrowed_book:
        return jsonify({'success': False, 'message': 'No record of this book being borrowed or it has already been returned.'})

    borrowed_book.return_date = datetime.now()

    book = Book.query.filter_by(id=book_id).first()
    if book:
        book.available += 1  
        db.session.commit()
        return jsonify({'success': True, 'message': 'Book returned successfully!'})
    else:
        return jsonify({'success': False, 'message': 'Book not found in the library.'})

@app.route('/categories')
def get_categories():
    categories = db.session.query(Book.category).distinct().all()
    category_list = [category[0] for category in categories]  
    return {"categories": category_list}

@app.route('/report')
def report():
    category = request.args.get('category')
    author = request.args.get('author')
    book_name = request.args.get('book_name')
    all_books = request.args.get('all') == 'true'

    if all_books:
        books = Book.query.all()
    else:
        query = "SELECT * FROM books WHERE 1=1"
        params = {}

        if category:
            query += " AND category = :category"
            params['category'] = category
        if author:
            query += " AND author = :author"
            params['author'] = author
        if book_name:
            query += " AND title = :book_name"
            params['book_name'] = book_name
        
        result = db.session.execute(text(query), params)
        books = result.fetchall()

    total_count = len(books)
    total_available = sum(book.available for book in books)

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
