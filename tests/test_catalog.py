from collections import Counter
import random
import pytest
from fastapi.testclient import TestClient
from taylor_lab.structures import RadixIndex, FrequencyTable, normalize
from taylor_lab.catalog import Catalog
from taylor_lab.api import create_app


def test_radix_edge_splits_and_duplicates():
    tree = RadixIndex()
    titles = ['All', 'All Too Well', 'All Too Well', 'August', 'Árvore', 'Paper', 'Paper Satellites']
    for i, t in enumerate(titles):
        tree.insert(t, i)
    for prefix in ['', 'all', 'all too', 'a', 'arv', 'paper s', 'notfound', '!!!']:
        assert sorted(tree.search(prefix)) == [i for i, t in enumerate(titles) if normalize(t).startswith(normalize(prefix))]


def test_frequency_collisions_and_resize():
    table = FrequencyTable(4)
    table.hash = lambda _: 0  # Force every key into the same bucket.
    words = ['word' + str(i % 79) for i in range(1000)]
    for w in words:
        table.add(w)
    assert dict(table.items()) == dict(Counter(words))


def test_radix_randomized_against_linear_scan():
    rng = random.Random(42)
    titles = [''.join(rng.choice('abcde') for _ in range(rng.randint(1, 15))) for _ in range(400)]
    tree = RadixIndex()
    for i, title in enumerate(titles):
        tree.insert(title, i)
    for title in titles[:100]:
        prefix = title[:3]
        assert sorted(tree.search(prefix)) == [i for i, t in enumerate(titles) if t.startswith(prefix)]


def test_invalid_batch_is_atomic(tmp_path):
    c = Catalog(tmp_path / 'x.sqlite3')
    with pytest.raises(ValueError):
        c.upsert([{'name': 'Valid', 'external_id': '1'}, {'name': '', 'external_id': '2'}], 'test')
    assert c.tracks() == []


def test_api_and_recommendations(tmp_path):
    with TestClient(create_app(tmp_path / 'api.sqlite3')) as client:
        assert client.get('/health').status_code == 200
        assert client.get('/api/analytics').json()['tracks'] == 6
        rows = client.get('/api/tracks?prefix=paper').json()
        assert len(rows) == 2
        similar = client.get('/api/recommend/' + str(rows[0]['id'])).json()
        assert similar[0]['track']['name'] == 'Neon Rivers'
        assert client.get('/api/recommend/999').status_code == 400
        assert client.get('/api/recommend/1?k=500').status_code == 422


def test_missing_features_not_fabricated(tmp_path):
    c = Catalog(tmp_path / 'catalog.sqlite3')
    row = {'external_id': 'itunes:1', 'name': 'Metadata only'}
    c.upsert([row], 'test')
    c.upsert([row], 'test')
    assert len(c.tracks()) == 1
    assert c.summary()['feature_rows'] == 0
    with pytest.raises(ValueError, match='incomplete'):
        c.recommend(c.tracks()[0]['id'])
