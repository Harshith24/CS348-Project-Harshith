from flask import Flask, send_from_directory, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy

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

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)

@app.route('/')
def main_page():
    return 'Home page'

@app.route('/home')
def serve():
    return send_from_directory(app.static_folder, 'index.html')

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
    
    # Query the database based on provided filters
    query = Book.query
    if all_books:
        books = query.all()
    else:
        if category:
            query = query.filter(Book.category == category)
        if author:
            query = query.filter(Book.author.ilike(f'%{author}%'))
        if book_name:
            query = query.filter(Book.title.ilike(f'%{book_name}%'))
        books = query.all()

    # Calculate the total count and availability of the filtered books
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
