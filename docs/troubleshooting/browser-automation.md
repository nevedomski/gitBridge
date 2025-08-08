# Browser Automation Troubleshooting

## Verify Playwright installation

```bash
python -c "import playwright; print('ok')" || pip install playwright
playwright install chromium
```

## Run in headless mode

```bash
gitbridge sync --method browser --headless
```

## Try a different browser

```bash
gitbridge sync --method browser --browser-type firefox
```
