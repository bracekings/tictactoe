"""
Single-file Flask app that serves a minimal frontend and provides Scryfall-backed
search and a per-session SQLite collection. Camera OCR scanning is handled client-side
using Tesseract.js which the page loads from CDN.

Run:
  python mtg_scanner.py

Open http://127.0.0.1:5000/
"""
from flask import Flask, request, jsonify, session, make_response
import sqlite3, os, uuid, requests
from datetime import datetime

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, 'cards.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
  # Always ensure DB exists and the collections table is present.
  conn = get_db()
  cur = conn.cursor()
  cur.execute('''
  CREATE TABLE IF NOT EXISTS collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    scryfall_id TEXT NOT NULL,
    name TEXT,
    image_uri TEXT,
    added_at TEXT
  )
  ''')
  conn.commit()
  conn.close()

init_db()
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', str(uuid.uuid4()))

SCRYFALL_SEARCH = 'https://api.scryfall.com/cards/search'
SCRYFALL_CARD = 'https://api.scryfall.com/cards/'


@app.before_request
def ensure_user():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())


@app.route('/')
def index():
    html = """
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width,initial-scale=1" />
        <title>MTG Scanner</title>
        <style>
        body{font-family:Arial,Helvetica,sans-serif;margin:0;padding:0}
        header{display:flex;gap:8px;align-items:center;padding:12px;background:#222;color:#fff}
        main{display:flex;gap:16px;padding:12px}
        #results{flex:2}
        #collection{flex:1;border-left:1px solid #ddd;padding-left:12px}
        article.card{display:flex;gap:8px;padding:8px;border:1px solid #ccc;margin-bottom:8px}
        article.card img{height:80px}
        #scanner{flex-basis:320px}
        video{width:320px;height:180px;border:1px solid #444}
        </style>
      </head>
      <body>
        <header>
          <h1>MTG Card Browser & Scanner</h1>
          <input id="search" placeholder="Search cards by name" />
          <button id="searchBtn">Search</button>
        </header>
        <main>
          <section id="results"></section>
          <section id="collection">
            <h2>Your Collection</h2>
            <ul id="mycol"></ul>
          </section>
          <section id="scanner">
            <h2>Camera Scanner</h2>
            <video id="video" autoplay playsinline></video>
            <canvas id="canvas" style="display:none"></canvas>
            <button id="scanBtn">Scan Card</button>
          </section>
        </main>
        <script src="https://unpkg.com/tesseract.js@4.0.2/dist/tesseract.min.js"></script>
        <script>
        const searchInput = document.getElementById('search')
        const searchBtn = document.getElementById('searchBtn')
        const results = document.getElementById('results')
        const mycol = document.getElementById('mycol')
        const video = document.getElementById('video')
        const canvas = document.getElementById('canvas')
        const scanBtn = document.getElementById('scanBtn')

        async function search(q){
          const res = await fetch('/api/search?q=' + encodeURIComponent(q))
          const data = await res.json()
          results.innerHTML = ''
          if(data.data){
            data.data.forEach(c => {
              const a = document.createElement('article')
              a.className = 'card'
              a.innerHTML = `<img src="${c.image_uris?.small||''}" alt=""><div><strong>${c.name}</strong><div>${c.type_line||''}</div><button data-id="${c.id}" data-name="${c.name}" data-img="${c.image_uris?.normal||''}">Add</button></div>`
              a.querySelector('button').addEventListener('click', ()=>addToCollection(c))
              results.appendChild(a)
            })
          } else {
            results.textContent = JSON.stringify(data)
          }
        }

        async function addToCollection(card){
          await fetch('/api/collection', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({scryfall_id:card.id, name:card.name, image_uri:card.image_uris?.small})})
          loadCollection()
        }

        async function loadCollection(){
          const res = await fetch('/api/collection')
          const data = await res.json()
          mycol.innerHTML = ''
          data.forEach(item=>{
            const li = document.createElement('li')
            li.innerHTML = `<img src="${item.image_uri||''}" style="height:40px;vertical-align:middle;margin-right:8px"><strong>${item.name}</strong> <button data-id="${item.id}">Remove</button>`
            li.querySelector('button').addEventListener('click', async ()=>{
              await fetch('/api/collection', {method:'DELETE', headers:{'Content-Type':'application/json'}, body:JSON.stringify({id:item.id})})
              loadCollection()
            })
            mycol.appendChild(li)
          })
        }

        searchBtn.addEventListener('click', ()=>search(searchInput.value))
        searchInput.addEventListener('keydown', (e)=>{ if(e.key==='Enter') search(searchInput.value) })

        async function startCamera(){
          const stream = await navigator.mediaDevices.getUserMedia({video:{facingMode:'environment'}})
          video.srcObject = stream
        }

        scanBtn.addEventListener('click', async ()=>{
          canvas.width = video.videoWidth
          canvas.height = video.videoHeight
          const ctx = canvas.getContext('2d')
          ctx.drawImage(video,0,0)
          const dataUrl = canvas.toDataURL('image/jpeg')
          results.textContent = 'Scanning OCR...'
          const { data: { text } } = await Tesseract.recognize(dataUrl, 'eng')
          const resp = await fetch('/api/identify', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({text})})
          const js = await resp.json()
          if(js.data && js.data.length>0){
            searchInput.value = js.data[0].name
            search(js.data[0].name)
          } else {
            results.textContent = 'No matches from OCR text.'
          }
        })

        startCamera().catch(e=>{ console.warn('camera failed', e); document.getElementById('scanner').style.display='none' })
        loadCollection()
        </script>
      </body>
    </html>
    """
    resp = make_response(html)
    resp.headers['Content-Type'] = 'text/html'
    return resp


@app.route('/api/search')
def api_search():
    q = request.args.get('q', '')
    page = request.args.get('page', None)
    params = {'q': q}
    if page:
        params['page'] = page
    resp = requests.get(SCRYFALL_SEARCH, params=params)
    return (resp.content, resp.status_code, {'Content-Type': 'application/json'})


@app.route('/api/card/<card_id>')
def api_card(card_id):
    resp = requests.get(SCRYFALL_CARD + card_id)
    return (resp.content, resp.status_code, {'Content-Type': 'application/json'})


@app.route('/api/identify', methods=['POST'])
def api_identify():
    data = request.json or {}
    text = data.get('text', '')
    if not text:
        return jsonify({'error': 'no text provided'}), 400
    params = {'q': f'!"{text}"'}
    resp = requests.get(SCRYFALL_SEARCH, params=params)
    return (resp.content, resp.status_code, {'Content-Type': 'application/json'})


@app.route('/api/collection', methods=['GET', 'POST', 'DELETE'])
def api_collection():
    user_id = session.get('user_id')
    conn = get_db()
    cur = conn.cursor()
    if request.method == 'GET':
        cur.execute('SELECT * FROM collections WHERE user_id = ?', (user_id,))
        rows = cur.fetchall()
        res = [dict(r) for r in rows]
        return jsonify(res)
    elif request.method == 'POST':
        data = request.json or {}
        scryfall_id = data.get('scryfall_id')
        name = data.get('name')
        image_uri = data.get('image_uri')
        if not scryfall_id:
            return jsonify({'error': 'missing scryfall_id'}), 400
        cur.execute('INSERT INTO collections (user_id, scryfall_id, name, image_uri, added_at) VALUES (?, ?, ?, ?, ?)',
                    (user_id, scryfall_id, name, image_uri, datetime.utcnow().isoformat()))
        conn.commit()
        return jsonify({'ok': True}), 201
    elif request.method == 'DELETE':
        data = request.json or {}
        item_id = data.get('id')
        if not item_id:
            return jsonify({'error': 'missing id'}), 400
        cur.execute('DELETE FROM collections WHERE id = ? AND user_id = ?', (item_id, user_id))
        conn.commit()
        return jsonify({'ok': True})


if __name__ == '__main__':
  import os
  port = int(os.environ.get('PORT', 5000))
  app.run(host='0.0.0.0', port=port, debug=True)
