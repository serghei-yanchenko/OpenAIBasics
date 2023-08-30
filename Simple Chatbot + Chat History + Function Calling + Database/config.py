from tempfile import mkdtemp
import flask
import openai
from flask_session import Session
import os

# Flask app config
app = flask.Flask(__name__)

app.secret_key = os.environ.get('FLASK_SECRET_KEY')
if app.secret_key is None:
    raise ValueError("FLASK_SECRET_KEY must be set in the environment")


# configure sessions
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False  # set session to not be permanent
app.config['SESSION_USE_SIGNER'] = True  # securely sign session cookies
app.config['SESSION_FILE_DIR'] = mkdtemp()  # create a temp directory for session files

sess = Session()
sess.init_app(app)



#OpenAI config
OpenAIAPIkey= os.environ.get('OPEN_AI_KEY')
OpenAIOrgKey= os.environ.get('OPEN_AI_ORG_KEY')

openai.organization = OpenAIOrgKey
openai.api_key = OpenAIAPIkey