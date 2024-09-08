from flask import Flask, send_from_directory

app = Flask(__name__, static_folder='frontend/build')

@app.route('/')
def main_page():
    return 'Main Page'

@app.route('/helloworld')
def serve():
    return send_from_directory(app.static_folder, 'index.html')


if __name__ == '__main__':
    app.run(debug=True)
