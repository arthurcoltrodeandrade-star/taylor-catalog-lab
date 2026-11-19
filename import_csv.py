"""Import the original local CSV without redistributing the dataset."""
import argparse
from taylor_lab.catalog import Catalog

p = argparse.ArgumentParser()
p.add_argument('csv', help='Path to taylor_swift_spotify.csv')
p.add_argument('--db', default='data/catalog.sqlite3')
args = p.parse_args()
print({'imported': Catalog(args.db).import_csv(args.csv)})
