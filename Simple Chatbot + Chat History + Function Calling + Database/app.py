from flask import render_template
from config import app
from gpt_routes_test import gpt_bp


app.register_blueprint(gpt_bp)

@app.route('/')
def index():
    return render_template('index.html')



if __name__ == '__main__':
    app.run(debug=True)


