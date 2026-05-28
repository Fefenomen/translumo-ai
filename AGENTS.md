# Translumo-AI — Agent Notes

## Mandatory: Run tests after every implementation

```bash
cd /home/fefenomen/Documents/projet/trad/translumo-ai
python -m pytest tests/ -v 2>&1
```

All tests must pass before pushing to GitHub.

## Debug mode

```bash
python3 main.py --debug
```

Prints OCR output, translation input/output, debounce state to console.

## Common bugs to watch for

1. **Widget creation outside main thread** — All `QWidget` creation/modification must happen in the main thread. Use `pyqtSignal(list)` + `@pyqtSlot(list)` for cross-thread overlay updates.

2. **Debounce never triggers** — `text_significantly_different()` compares normalized text. If OCR returns unstable whitespace/newlines, `normalize_text()` handles it. If blocks change count/position each frame, the concat string changes and debounce resets.

3. **Batch translation parsing** — The LLM must preserve `---` separators. If it doesn't, `split("\n---\n")` returns a single part → fallback to original text for extra blocks.

4. **Spectacle capture** — On Wayland, `spectacle -b -n -o` captures full desktop. Cropping to region geometry must match. Global vs per-monitor coordinates can be off.

5. **Monitor selection** — `slurp -or` must be used. Store the returned geometry in `capture_region` for overlay positioning. Don't use `spectacle -m` (captures cursor-monitor, not clicked one).

6. **Overlay cleanup** — When killing the process, `aboutToQuit` signal destroys all overlays. Without this, Wayland keeps orphan overlay windows visible.

## Conventions

- `normalize_text()` before comparing OCR output for debounce
- `pyqtSignal` for all cross-thread communication
- `OverlayManager` pools/recycles widgets — never create/delete per frame
- Block dict keys: `x, y, w, h, text` (from OCR) + `original, translated` (post-translation)
