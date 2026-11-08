# Risk Runners Development Server

## Quick Start

### Start the Server
```bash
# On macOS/Linux
./start-server.sh

# On Windows
start-server.bat
```

The server will:
1. Update cache-busting parameters for JavaScript files
2. Start the development server on port 8000 (or next available port)
3. Display helpful links and information

## Cache Management

### Automatic Cache Busting
The server automatically adds version parameters to JavaScript includes (e.g., `script.js?v=1234567890`) to prevent browser caching issues during development.

### Manual Cache Clearing
If you're still seeing old JavaScript behavior:

```bash
# Clear cache manually
python3 clear-cache.py

# Then hard refresh your browser (Ctrl+F5 or Cmd+Shift+R)
```

### Browser Cache Issues
If you're getting different results on different ports, it's likely due to browser caching. Try:

1. **Hard refresh**: Ctrl+F5 (Windows/Linux) or Cmd+Shift+R (Mac)
2. **Disable cache**: Open browser dev tools → Network tab → check "Disable cache"
3. **Incognito mode**: Test in a private/incognito window
4. **Clear browser data**: Clear site data for localhost

## Server Features

- **CORS enabled**: Allows cross-origin requests for development
- **Aggressive cache control**: Prevents caching of JavaScript and JSON files
- **Auto port selection**: Finds available port if 8000 is taken
- **Cache-busting**: Automatic versioning of JavaScript files

## Files

- `serve.py` - Main server script with enhanced cache control
- `start-server.sh` / `start-server.bat` - Server startup scripts
- `update-cache-busting.py` - Updates HTML files with cache-busting parameters
- `clear-cache.py` - Manual cache clearing utility

## Troubleshooting

### JavaScript Changes Not Appearing
1. Check if the server updated cache-busting parameters
2. Look for `?v=timestamp` in script src attributes
3. Hard refresh the browser
4. Check browser dev tools for 304 (cached) responses

### Port Issues
The server automatically finds an available port between 8000-8010. If all ports are taken, it will exit with an error.

### Python Issues
Make sure Python 3 is installed and available in your PATH. The scripts will try both `python3` and `python` commands.