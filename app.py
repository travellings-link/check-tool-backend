import flask
import flask_cors

app = flask.Flask('__name__')

flask_cors.CORS(app,
                origins=["http://localhost:5173", "https://check-tool.travellings.cn"],
                supports_credentials=True,
                allow_headers=["Content-Type", "Authorization", "Cookie"]
                )

from abnormal import abnormal_bp
from checkerror import checkerror_bp
from login import login_bp
from sites import sites_bp

app.register_blueprint(abnormal_bp, url_prefix='/')
app.register_blueprint(checkerror_bp, url_prefix='/')
app.register_blueprint(login_bp, url_prefix='/')
app.register_blueprint(sites_bp, url_prefix='/')

if __name__ == '__main__':
   app.run(debug=False)