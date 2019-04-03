""" This file is used to start application"""
from app import app

if __name__ == "__main__":
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run(debug=False)
