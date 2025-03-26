from flask import Flask, render_template, jsonify
import json

app = Flask(__name__)

@app.route('/')
def dashboard():
    # Load dashboard data from the JSON file
    with open('dashboard_data.json', 'r') as f:
        data = json.load(f)

    # Extract trends and deltas for the template
    trends = data['trends']
    deltas = data['deltas']

    return render_template('dashboard.html', trends=trends, deltas=deltas)

if __name__ == '__main__':
    app.run(debug=True)
