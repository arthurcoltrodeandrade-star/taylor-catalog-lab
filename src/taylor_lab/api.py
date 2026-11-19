from contextlib import asynccontextmanager
import json
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
import httpx
from .catalog import Catalog

ROOT = Path(__file__).parent


def create_app(db_path=None):
    catalog = Catalog(db_path or os.getenv('TAYLOR_DB', 'data/catalog.sqlite3'))

    @asynccontextmanager
    async def lifespan(app):
        catalog.upsert(json.loads((ROOT / 'data/demo.json').read_text()), 'Synthetic demo audio features, not measured recordings')
        yield

    app = FastAPI(title='Taylor Catalog Lab', version='0.1.0', lifespan=lifespan)

    @app.get('/')
    def home():
        return FileResponse(ROOT / 'static/index.html')

    @app.get('/health')
    def health():
        return {'status': 'ok'}

    @app.get('/api/tracks')
    def tracks(prefix: str = Query('', max_length=150), album: str | None = None):
        return catalog.tracks(prefix, album)

    @app.get('/api/analytics')
    def analytics():
        return catalog.summary()

    @app.get('/api/recommend/{track_id}')
    def recommend(track_id: int, k: int = Query(5, ge=1, le=20)):
        try:
            return catalog.recommend(track_id, k)
        except ValueError as error:
            raise HTTPException(400, str(error)) from error

    @app.post('/api/import/itunes')
    def itunes():
        # Fixed artist + endpoint: no arbitrary URL or query supplied by the browser.
        try:
            with httpx.Client(timeout=12, follow_redirects=False) as client:
                response = client.get('https://itunes.apple.com/lookup', params={
                    'id': '159260351', 'entity': 'song', 'limit': 200, 'country': 'fr'})
                response.raise_for_status()
                data = response.json()
            rows = [{'external_id': 'itunes:' + str(r['trackId']), 'name': r['trackName'],
                     'album': r.get('collectionName', 'Unknown'), 'duration_ms': r.get('trackTimeMillis', 0),
                     'release_date': r.get('releaseDate', '')[:10], 'store_url': r.get('trackViewUrl', '')}
                    for r in data['results'] if r.get('kind') == 'song' and r.get('artistId') == 159260351]
            return {'imported': catalog.upsert(rows, 'Apple iTunes public catalog metadata'),
                    'note': 'Audio features are unavailable for these tracks. This is a bounded catalog sample.'}
        except (httpx.HTTPError, ValueError, KeyError) as error:
            raise HTTPException(502, 'iTunes catalog unavailable. Offline demo remains usable.') from error

    return app


app = create_app()
