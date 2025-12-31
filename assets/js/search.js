// Enhanced Search Functionality for Risk Runners
class RiskRunnersSearch {
    constructor() {
        this.searchInput = document.getElementById('searchInput');
        this.searchResults = document.getElementById('searchResults');
        this.filterButtons = document.querySelectorAll('.filter-btn');
        this.fuse = null;
        this.searchData = [];
        this.currentFilter = 'all';
        this.maxDisplayResults = 50;
        this.searchTimeout = null;
        
        this.init();
    }
    
    async init() {
        try {
            console.log('Initializing search functionality...');
            await this.loadSearchIndex();
            console.log(`Search index loaded: ${this.searchData.length} items`);
            this.setupEventListeners();
            this.updateStats();
        } catch (error) {
            console.error('Failed to initialize search:', error);
            this.showError(`Failed to load search functionality: ${error.message}`);
        }
    }
    
    async loadSearchIndex() {
        // Try multiple possible paths for the search index
        const possiblePaths = [
            'data/002_search-index.json',
            './data/002_search-index.json',
            '../data/002_search-index.json',
            '/data/002_search-index.json'
        ];
        
        let lastError = null;
        
        for (const path of possiblePaths) {
            try {
                console.log('Attempting to load search index from:', path);
                const response = await fetch(path);
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                this.searchData = await response.json();
                console.log(`Successfully loaded search index: ${this.searchData.length} items from ${path}`);
                
                // Configure Fuse.js for fuzzy search
                const fuseOptions = {
                    keys: [
                        { name: 'title', weight: 0.7 },
                        { name: 'type', weight: 0.2 },
                        { name: 'source_file', weight: 0.1 }
                    ],
                    threshold: 0.3,
                    includeScore: true,
                    includeMatches: true,
                    minMatchCharLength: 2
                };
                
                this.fuse = new Fuse(this.searchData, fuseOptions);
                console.log(`Search index loaded: ${this.searchData.length} items`);
                return; // Success, exit the function
                
            } catch (error) {
                console.warn(`Failed to load from ${path}:`, error.message);
                lastError = error;
                continue; // Try next path
            }
        }
        
        // If we get here, all paths failed
        console.error('Failed to load search index from all attempted paths');
        console.error('Last error:', lastError);
        throw new Error(`Failed to load search index. Last error: ${lastError?.message || 'Unknown error'}`);
    }
    
    setupEventListeners() {
        // Search input with debouncing
        this.searchInput.addEventListener('input', (e) => {
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => {
                this.performSearch(e.target.value.trim());
            }, 300);
        });
        
        // Clear search on empty input
        this.searchInput.addEventListener('search', () => {
            if (this.searchInput.value === '') {
                this.clearResults();
            }
        });
        
        // Filter buttons
        this.filterButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.setActiveFilter(e.target.dataset.filter);
                this.performSearch(this.searchInput.value.trim());
            });
        });
        
        // Keyboard navigation
        this.searchInput.addEventListener('keydown', (e) => {
            this.handleKeyboardNavigation(e);
        });
        
        // Click outside to close results
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.search-container')) {
                this.hideResults();
            }
        });
    }
    
    setActiveFilter(filter) {
        this.currentFilter = filter;
        this.filterButtons.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.filter === filter);
        });
    }
    
    performSearch(query) {
        if (!query || query.length < 2) {
            this.clearResults();
            return;
        }
        
        if (!this.fuse) {
            this.showError('Search not ready. Please try again.');
            return;
        }
        
        // Perform fuzzy search
        let results = this.fuse.search(query);
        
        // Apply filter if not 'all'
        if (this.currentFilter !== 'all') {
            results = results.filter(result => 
                result.item.type === this.currentFilter
            );
        }
        
        this.displayResults(results, query);
    }
    
    displayResults(results, query) {
        this.searchResults.innerHTML = '';
        
        if (results.length === 0) {
            this.showNoResults(query);
            return;
        }
        
        // For company searches, group by company and show unique companies
        const companyResults = this.getUniqueCompanies(results);
        
        if (companyResults.length > 0) {
            this.addTypeHeader('Companies', companyResults.length);
            
            const displayResults = companyResults.slice(0, 10);
            displayResults.forEach(company => {
                this.addCompanyResultItem(company, query);
            });
            
            if (companyResults.length > 10) {
                this.addMoreResultsIndicator(companyResults.length - 10);
            }
        }
        
        this.showResults();
    }
    
    getUniqueCompanies(results) {
        const companyMap = new Map();
        
        results.forEach(result => {
            const item = result.item;
            const companyFile = item.source_file;
            
            if (!companyMap.has(companyFile)) {
                const companyName = this.formatCompanyName(companyFile);
                companyMap.set(companyFile, {
                    name: companyName,
                    filename: companyFile,
                    url: companyFile, // Direct link to company file
                    industries: new Set(),
                    exposures: new Set(),
                    eventCodes: new Set(),
                    score: result.score
                });
            }
            
            const company = companyMap.get(companyFile);
            
            // Categorize the data
            switch (item.type) {
                case 'Industry':
                    company.industries.add(item.title);
                    break;
                case 'Exposure':
                    company.exposures.add(item.title);
                    break;
                case 'Event Code':
                    company.eventCodes.add(item.title);
                    break;
            }
        });
        
        return Array.from(companyMap.values())
            .sort((a, b) => a.score - b.score); // Sort by relevance
    }
    
    formatCompanyName(filename) {
        // Remove .html extension and format the company name
        let name = filename.replace('.html', '');
        
        // Handle special cases and add spaces
        name = name
            .replace(/([A-Z])/g, ' $1')
            .replace(/INC$/, 'Inc')
            .replace(/CORP$/, 'Corp')
            .replace(/CO$/, 'Co')
            .replace(/LTD$/, 'Ltd')
            .replace(/LLC$/, 'LLC')
            .trim();
        
        // Capitalize first letter of each word properly
        return name.split(' ')
            .map(word => {
                if (word.length <= 2) return word.toUpperCase();
                return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
            })
            .join(' ');
    }
    
    addCompanyResultItem(company, query) {
        const li = document.createElement('li');
        li.className = 'search-result-item';
        
        const primaryIndustry = Array.from(company.industries)[0] || 'Various Industries';
        const riskCount = company.exposures.size + company.eventCodes.size;
        
        li.innerHTML = `
            <a href="${company.url}" class="result-link">
                <div class="result-title">${this.highlightMatches(company.name, [], query)}</div>
                <div class="result-meta">
                    <span class="result-type">Company</span>
                    <span class="result-separator">•</span>
                    <span class="result-source">${primaryIndustry}</span>
                    <span class="result-separator">•</span>
                    <span class="result-source">${riskCount} Risk Factors</span>
                </div>
            </a>
        `;
        
        this.searchResults.appendChild(li);
    }
    
    addTypeHeader(type, count) {
        const header = document.createElement('li');
        header.className = 'search-type-header';
        header.innerHTML = `
            <div class="type-header-content">
                <span class="type-name">${this.getTypeIcon(type)} ${type}</span>
                <span class="type-count">${count}</span>
            </div>
        `;
        this.searchResults.appendChild(header);
    }
    
    addResultItem(result, query) {
        const item = result.item;
        const li = document.createElement('li');
        li.className = 'search-result-item';
        
        // Highlight matching text
        const highlightedTitle = this.highlightMatches(item.title, result.matches, query);
        
        li.innerHTML = `
            <a href="${item.url}" class="result-link">
                <div class="result-title">${highlightedTitle}</div>
                <div class="result-meta">
                    <span class="result-type">${item.type}</span>
                    <span class="result-separator">•</span>
                    <span class="result-source">${this.formatSourceFile(item.source_file)}</span>
                    ${result.score ? `<span class="result-score">${Math.round((1 - result.score) * 100)}% match</span>` : ''}
                </div>
            </a>
        `;
        
        this.searchResults.appendChild(li);
    }
    
    highlightMatches(text, matches, query) {
        if (!matches || matches.length === 0) {
            return this.escapeHtml(text);
        }
        
        // Simple highlighting - can be enhanced
        const regex = new RegExp(`(${this.escapeRegex(query)})`, 'gi');
        return this.escapeHtml(text).replace(regex, '<mark>$1</mark>');
    }
    
    addMoreResultsIndicator(count) {
        const li = document.createElement('li');
        li.className = 'more-results-indicator';
        li.innerHTML = `
            <div class="more-results-content">
                <span>+${count} more results</span>
                <small>Refine your search to see more specific results</small>
            </div>
        `;
        this.searchResults.appendChild(li);
    }
    
    showNoResults(query) {
        this.searchResults.innerHTML = `
            <li class="no-results">
                <div class="no-results-content">
                    <div class="no-results-icon">🔍</div>
                    <div class="no-results-text">
                        <strong>No results found for "${this.escapeHtml(query)}"</strong>
                        <p>Try adjusting your search terms or filters</p>
                    </div>
                </div>
            </li>
        `;
        this.showResults();
    }
    
    showError(message) {
        this.searchResults.innerHTML = `
            <li class="search-error">
                <div class="error-content">
                    <span class="error-icon">⚠️</span>
                    <span class="error-message">${this.escapeHtml(message)}</span>
                </div>
            </li>
        `;
        this.showResults();
    }
    
    showResults() {
        this.searchResults.style.display = 'block';
        this.searchResults.classList.add('fade-in');
    }
    
    hideResults() {
        this.searchResults.style.display = 'none';
    }
    
    clearResults() {
        this.searchResults.innerHTML = '';
        this.hideResults();
    }
    
    handleKeyboardNavigation(e) {
        const items = this.searchResults.querySelectorAll('.result-link');
        if (items.length === 0) return;
        
        let currentIndex = -1;
        const currentActive = this.searchResults.querySelector('.result-link.keyboard-active');
        
        if (currentActive) {
            currentIndex = Array.from(items).indexOf(currentActive);
            currentActive.classList.remove('keyboard-active');
        }
        
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                currentIndex = Math.min(currentIndex + 1, items.length - 1);
                break;
            case 'ArrowUp':
                e.preventDefault();
                currentIndex = Math.max(currentIndex - 1, 0);
                break;
            case 'Enter':
                if (currentActive) {
                    e.preventDefault();
                    currentActive.click();
                }
                return;
            case 'Escape':
                this.hideResults();
                this.searchInput.blur();
                return;
            default:
                return;
        }
        
        if (currentIndex >= 0 && items[currentIndex]) {
            items[currentIndex].classList.add('keyboard-active');
            items[currentIndex].scrollIntoView({ block: 'nearest' });
        }
    }
    
    updateStats() {
        // Update company count if element exists
        const totalCompaniesEl = document.getElementById('totalCompanies');
        if (totalCompaniesEl && this.searchData.length > 0) {
            // Count unique source files (companies)
            const uniqueCompanies = new Set(this.searchData.map(item => item.source_file));
            totalCompaniesEl.textContent = `${uniqueCompanies.size}+`;
        }
    }
    
    // Utility methods
    getTypeIcon(type) {
        const icons = {
            'Industry': '🏭',
            'Exposure': '⚠️',
            'Event Code': '📊',
            'Other': '📄'
        };
        return icons[type] || '📄';
    }
    
    formatSourceFile(filename) {
        return filename.replace('.html', '').replace(/([A-Z])/g, ' $1').trim();
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }
}

// Initialize search when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new RiskRunnersSearch();
});