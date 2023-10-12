from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    users = [
        {'name': 'John', 'age': 25},
        {'name': 'Jane', 'age': 22},
        {'name': 'Dave', 'age': 32},
        {'name': 'Doe', 'age': 45}
    ]
    return render_template('index.html', users=users)

if __name__ == '__main__':
    app.run(debug=True)