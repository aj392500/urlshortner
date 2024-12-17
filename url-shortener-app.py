from flask import Flask, request, redirect, render_template
import sqlite3
import string
import random
import os

app = Flask(__name__)
DATABASE = 'urlshortener.db'

def init_db():
    """Initialize the SQLite database for storing URL mappings"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS urls (
            short_code TEXT PRIMARY KEY,
            original_url TEXT NOT NULL,
            click_count INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def generate_short_code(length=6):
    """Generate a unique short code for URLs"""
    characters = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choice(characters) for _ in range(length))
        
        # Check if code is unique
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('SELECT * FROM urls WHERE short_code = ?', (code,))
        if not c.fetchone():
            conn.close()
            return code

@app.route('/', methods=['GET', 'POST'])
def index():
    """Main page for creating short URLs"""
    if request.method == 'POST':
        original_url = request.form['url']
        
        # Basic URL validation
        if not original_url.startswith(('http://', 'https://')):
            original_url = 'http://' + original_url
        
        # Generate short code
        short_code = generate_short_code()
        
        # Save to database
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('INSERT INTO urls (short_code, original_url) VALUES (?, ?)', 
                  (short_code, original_url))
        conn.commit()
        conn.close()
        
        # Return the generated short URL
        short_url = request.host_url + short_code
        return render_template('index.html', short_url=short_url)
    
    return render_template('index.html')

@app.route('/<short_code>')
def redirect_to_url(short_code):
    """Redirect short code to original URL and track clicks"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    c.execute('SELECT original_url FROM urls WHERE short_code = ?', (short_code,))
    result = c.fetchone()
    
    if result:
        # Increment click count
        c.execute('UPDATE urls SET click_count = click_count + 1 WHERE short_code = ?', 
                  (short_code,))
        conn.commit()
        conn.close()
        
        return redirect(result[0])
    
    conn.close()
    return 'URL not found', 404

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
