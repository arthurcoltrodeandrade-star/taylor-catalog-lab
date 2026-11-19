from collections import defaultdict
from contextlib import contextmanager
import csv
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sqlite3
from .structures import RadixIndex, FrequencyTable, normalize

FEATURES = ('acousticness', 'danceability', 'energy', 'valence', 'tempo')


class Catalog:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS tracks(
                id INTEGER PRIMARY KEY, external_id TEXT UNIQUE, name TEXT, album TEXT,
                duration_ms INTEGER, release_date TEXT, features TEXT, provenance TEXT,
                imported_at TEXT, store_url TEXT)''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def upsert(self, records, provenance):
        # Validate the entire batch before opening the write transaction.
        rows = []
        for r in records:
            name = str(r.get('name', '')).strip()
            external_id = str(r.get('external_id', '')).strip()
            if not name or not external_id or not normalize(name):
                raise ValueError('Each track needs a nonempty title and external_id.')
            duration = int(r.get('duration_ms', 0))
            if duration < 0:
                raise ValueError('Duration cannot be negative.')
            features = {}
            for feature in FEATURES:
                value = r.get(feature)
                if value is not None and value != '':
                    number = float(value)
                    if not math.isfinite(number) or not 0 <= number <= (400 if feature == 'tempo' else 1):
                        raise ValueError(f'Invalid audio feature: {feature}')
                    features[feature] = number
            rows.append((external_id, name, str(r.get('album', 'Unknown')), duration,
                         str(r.get('release_date', '')), json.dumps(features), provenance,
                         datetime.now(timezone.utc).isoformat(), str(r.get('store_url', ''))))
        with self.connect() as db:
            db.executemany('''INSERT INTO tracks(external_id,name,album,duration_ms,release_date,
                features,provenance,imported_at,store_url) VALUES(?,?,?,?,?,?,?,?,?)
                ON CONFLICT(external_id) DO UPDATE SET name=excluded.name, album=excluded.album,
                duration_ms=excluded.duration_ms,release_date=excluded.release_date,
                features=excluded.features,provenance=excluded.provenance,
                imported_at=excluded.imported_at,store_url=excluded.store_url''', rows)
        return len(rows)

    def tracks(self, prefix='', album=None):
        with self.connect() as db:
            rows = [dict(r) for r in db.execute('SELECT * FROM tracks ORDER BY name,id')]
        for r in rows:
            r['features'] = json.loads(r['features'])
        if prefix:
            index = RadixIndex()
            for r in rows:
                index.insert(r['name'], r['id'])
            matches = set(index.search(prefix))
            rows = [r for r in rows if r['id'] in matches]
        return [r for r in rows if album is None or r['album'] == album]

    def summary(self):
        tracks = self.tracks()
        groups = defaultdict(list)
        words = FrequencyTable()
        for r in tracks:
            groups[r['album']].append(r)
            for word in normalize(r['name']).split():
                words.add(word)
        albums = []
        for name, group in sorted(groups.items()):
            averages = {}
            for f in FEATURES:
                vals = [r['features'][f] for r in group if f in r['features']]
                averages[f] = round(sum(vals) / len(vals), 3) if vals else None
            albums.append({'album': name, 'tracks': len(group), 'mean_features': averages,
                           'mean_duration_s': round(sum(r['duration_ms'] for r in group) / len(group) / 1000, 1)})
        return {'tracks': len(tracks), 'albums': albums, 'title_terms': words.items()[:15],
                'feature_rows': sum(all(f in r['features'] for f in FEATURES) for r in tracks)}

    def recommend(self, track_id, k=5):
        rows = [r for r in self.tracks() if all(f in r['features'] for f in FEATURES)]
        target = next((r for r in rows if r['id'] == track_id), None)
        if target is None:
            raise ValueError('Track missing or has incomplete audio features. iTunes metadata has no audio features.')
        # Standardize using catalog statistics so tempo does not dominate [0,1] features.
        means = {f: sum(r['features'][f] for r in rows) / len(rows) for f in FEATURES}
        scales = {f: math.sqrt(sum((r['features'][f] - means[f])**2 for r in rows) / len(rows)) or 1 for f in FEATURES}
        result = []
        for r in rows:
            if r['id'] == track_id:
                continue
            contributions = {f: ((r['features'][f] - target['features'][f]) / scales[f])**2 for f in FEATURES}
            result.append({'track': r, 'distance': round(math.sqrt(sum(contributions.values())), 4),
                           'closest_features': sorted(contributions, key=contributions.get)[:2]})
        return sorted(result, key=lambda x: (x['distance'], x['track']['id']))[:k]

    def import_csv(self, path):
        with open(path, newline='', encoding='utf-8-sig') as f:
            rows = list(csv.DictReader(f))
        for row in rows:
            row['external_id'] = 'spotify:' + row['id']
        return self.upsert(rows, 'User-supplied historical CSV. Not current Spotify metrics.')
