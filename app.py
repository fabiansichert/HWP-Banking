from banking import app

if __name__ == "__main__":
    app.config['SESSION_COOKIE_HTTPONLY'] = False
    app.run(debug=True, host="0.0.0.0", port=5000)