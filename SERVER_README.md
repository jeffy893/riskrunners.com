# Risk Runners Local Development Server

## Why do I need a server?

The Risk Runners website uses JavaScript to load data files (JSON) dynamically. Modern browsers block these requests when opening HTML files directly (`file://` protocol) for security reasons. A local HTTP server resolves this issue.

## Quick Start

### Option 1: Use the provided scripts

**On macOS/Linux:**
```bash
./start-server.sh
```

**On Windows:**
```batch
start-server.bat
```

### Option 2: Run Python directly

```bash
# Using Python 3
python3 serve.py

# Or if python3 isn't available
python serve.py
```

### Option 3: Use Python's built-in server (basic)

```bash
# Python 3
python3 -m http.server 8000

# Python 2 (not recommended)
python -m SimpleHTTPServer 8000
```

## Accessing the Website

Once the server is running, open your browser and go to:

- **Main website:** http://localhost:8000
- **Industry browser:** http://localhost:8000/companies/by-industry.html
- **Company directory:** http://localhost:8000/companies/directory.html

## Features of the Custom Server

The included `serve.py` script provides:

- ✅ CORS headers for proper JavaScript functionality
- ✅ Automatic port detection (tries 8000, 8001, etc.)
- ✅ Better logging and error messages
- ✅ Quick links display on startup

## Troubleshooting

### "Failed to fetch" errors
- Make sure you're accessing the site via `http://localhost:8000` (not opening files directly)
- Check that the server is running and showing no errors

### Port already in use
- The server will automatically try the next available port
- Or specify a different port: `python3 serve.py 8080`

### Python not found
- Install Python 3 from https://python.org
- Make sure Python is in your system PATH

## Alternative Servers

If you prefer other development servers:

**Node.js (if you have npm):**
```bash
npx http-server -p 8000 --cors
```

**PHP (if you have PHP):**
```bash
php -S localhost:8000
```

**Live Server (VS Code extension):**
- Install "Live Server" extension
- Right-click on `index.html` → "Open with Live Server"