# Risk Runners Website

A comprehensive wiki on publicly traded companies to help manage investment exposure and risk factors.

## 📁 Project Structure

```
riskrunners.com/
├── index.html              # Main homepage (modernized)
├── 000_index.html          # Original homepage (preserved)
├── 001_search.js           # Original search script (preserved)
├── assets/                 # Organized static assets
│   ├── css/
│   │   └── main.css        # Modern CSS styles
│   ├── js/
│   │   └── search.js       # Enhanced search functionality
│   └── images/             # Images and media files
├── data/                   # Data files and generators
│   ├── 002_search-index.json    # Search index data
│   └── 003_gen-search-index.py  # Search index generator
├── companies/              # Individual company HTML files (to be organized)
└── README.md              # This file
```

## 🚀 Features

### Enhanced Styling
- Modern CSS with CSS variables for consistent theming
- Responsive design for mobile and desktop
- Improved typography and spacing
- Professional color scheme
- Smooth animations and transitions

### Improved Search
- Debounced search input for better performance
- Keyboard navigation support (arrow keys, enter, escape)
- Enhanced error handling
- Better result highlighting
- Click tracking for analytics

### Better Organization
- Semantic HTML5 structure
- Accessibility improvements (ARIA labels, screen reader support)
- Organized file structure with logical directories
- SEO optimizations (meta tags, structured data)

## 🎨 Design Improvements

### Color Scheme
- Primary: #2c3e50 (Dark blue-gray)
- Secondary: #3498db (Blue)
- Accent: #e74c3c (Red)
- Success: #27ae60 (Green)
- Warning: #f39c12 (Orange)

### Typography
- Modern font stack: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif
- Improved hierarchy with consistent sizing
- Better line spacing for readability

### Layout
- Centered container with max-width for better readability
- Card-based design for content sections
- Grid layout for company listings
- Responsive breakpoints for mobile optimization

## 📱 Responsive Design

- **Desktop**: Full-width layout with multi-column grids
- **Tablet**: Adjusted spacing and simplified navigation
- **Mobile**: Single-column layout with touch-friendly elements

## 🔍 Search Enhancements

- **Fuzzy Search**: Powered by Fuse.js with weighted scoring
- **Keyboard Navigation**: Arrow keys to navigate, Enter to select
- **Debounced Input**: Reduces API calls and improves performance
- **Result Categorization**: Shows item type and source file
- **Error Handling**: Graceful fallbacks for network issues

## 🚀 Next Steps

1. **Move Company Files**: Organize individual company HTML files into the `/companies/` directory
2. **Add Favicon**: Create and add a favicon for better branding
3. **Optimize Images**: Compress and optimize any images
4. **Add Analytics**: Implement tracking for user interactions
5. **Progressive Web App**: Add service worker for offline functionality

## 🛠️ Development

The site uses vanilla HTML, CSS, and JavaScript with no build process required. Simply serve the files from a web server.

### Local Development
```bash
# Serve locally (Python 3)
python -m http.server 8000

# Or with Node.js
npx serve .
```

## 📊 Data Structure

The search index contains structured data about:
- **Industries**: Business sector classifications
- **Exposures**: Risk exposure categories
- **Event Codes**: Specific risk event types
- **Companies**: Individual company profiles with risk factors

Each entry includes:
- Title (searchable name)
- Type (Industry/Exposure/Event Code)
- URL (link to detailed page)
- Source file (originating company report)