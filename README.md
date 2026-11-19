# Taylor — music catalog and analysis

My original Python university project for exploring Taylor Swift's music catalog through a terminal menu. The program lists and searches songs, groups them by album or theme, displays YouTube view statistics, and counts words in lyrics.

This repository keeps the original implementation and Portuguese interface. The cleanup only separates the project source from the bundled Python runtime, normalizes blank lines/encoding, and reads the YouTube API key from an environment variable.

## Files

| File | Responsibility |
|---|---|
| `main.py` | Starts initialization and the main menu |
| `menu.py` | Terminal menus and user interaction |
| `arquivos.py` | Data initialization, file storage and YouTube integration |
| `operacoes.py` | Song details, album operations and charts |
| `patricia.py` | Original PATRICIA search-tree implementation |
| `hash.py` | Original hash table and word-frequency ordering |
| `junta-tudo.py` | Original scratch/experimentation script; use `main.py` to launch |

## Run

```sh
python -m pip install -r requirements.txt
python main.py
```

Run from this directory: the original program uses paths relative to the working directory. For YouTube requests, configure your own key before launching:

```powershell
$env:YOUTUBE_API_KEY="your-key"
python main.py
```

The original inputs are `taylor_swift_spotify.csv`, the per-album text files in `letras/` and `urls/`, and the generated `.bin` files. They are available locally from the original ZIP and excluded from this public repository. Copy them beside `main.py` to use your original data. A fresh initialization fetches YouTube statistics and requires the API key. Only load pickle-based `.bin` files from a source you trust.

The PATRICIA tree, hashing algorithm, storage format, plots and menu logic are preserved. There is no new web dashboard, FastAPI service, recommendation engine or synthetic dataset in this version.
