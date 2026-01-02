// Event Code Browser JavaScript
class EventCodeBrowser {
    constructor() {
        this.searchData = [];
        this.eventCodes = new Map();
        this.companies = new Map();
        this.filteredEventCodes = [];
        
        this.eventCodeGrid = document.getElementById('eventCodeGrid');
        this.eventCodeStats = document.getElementById('eventCodeStats');
        this.eventCodeSearch = document.getElementById('eventCodeSearch');
        
        this.init();
    }
    
    async init() {
        try {
            console.log('Initializing event code browser...');
            await this.loadData();
            console.log(`Loaded ${this.searchData.length} search entries`);
            this.processEventCodes();
            console.log(`Processed ${this.eventCodes.size} event codes`);
            this.displayEventCodes();
            this.setupSearch();
            this.updateStats();
        } catch (error) {
            console.error('Failed to initialize event code browser:', error);
            this.showError(`Failed to load event code data: ${error.message}`);
        }
    }
    
    async loadData() {
        // Determine the correct base path based on current location
        const currentPath = window.location.pathname;
        const isInCompaniesDir = currentPath.includes('/companies/');
        
        // Try different path strategies
        const pathStrategies = [
            // Strategy 1: Relative paths based on current location
            isInCompaniesDir ? '../data/002_search-index.json' : 'data/002_search-index.json',
            // Strategy 2: Try other relative paths
            '../data/002_search-index.json',
            './data/002_search-index.json',
            'data/002_search-index.json',
            // Strategy 3: Absolute paths from root
            '/riskrunners/riskrunners.com/data/002_search-index.json',
            '/data/002_search-index.json'
        ];
        
        let lastError = null;
        
        for (const path of pathStrategies) {
            try {
                console.log('Attempting to load search index from:', path);
                
                // Create absolute URL to avoid relative path issues
                const baseUrl = window.location.origin + window.location.pathname.replace(/\/[^\/]*$/, '/');
                const absoluteUrl = new URL(path, baseUrl);
                console.log('Resolved absolute URL:', absoluteUrl.href);
                
                const response = await fetch(absoluteUrl.href);
                
                console.log('Response status:', response.status);
                console.log('Response ok:', response.ok);
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status} - ${response.statusText}`);
                }
                
                const text = await response.text();
                console.log('Response text length:', text.length);
                
                if (text.length === 0) {
                    throw new Error('Empty response');
                }
                
                this.searchData = JSON.parse(text);
                console.log(`Successfully loaded ${this.searchData.length} search entries from ${path}`);
                return; // Success, exit the function
                
            } catch (error) {
                console.warn(`Failed to load from ${path}:`, error.message);
                lastError = error;
                continue; // Try next path
            }
        }
        
        // If we get here, all strategies failed
        throw new Error(`Failed to load search index from any path. Last error: ${lastError?.message || 'Unknown error'}`);
    }
    
    processEventCodes() {
        // Filter for event code entries only
        const eventCodeEntries = this.searchData.filter(item => item.type === 'Event Code');
        console.log(`Found ${eventCodeEntries.length} event code entries`);
        
        // Group companies by event code
        eventCodeEntries.forEach(entry => {
            const eventCodeName = entry.title;
            const companyFile = entry.source_file;
            const companyName = this.formatCompanyName(companyFile);
            
            // Track event codes
            if (!this.eventCodes.has(eventCodeName)) {
                this.eventCodes.set(eventCodeName, {
                    name: eventCodeName,
                    companies: new Map(), // Use Map instead of Set
                    icon: this.getEventCodeIcon(eventCodeName)
                });
            }
            
            // Add company to event code (Map will handle duplicates by filename)
            this.eventCodes.get(eventCodeName).companies.set(companyFile, {
                name: companyName,
                filename: companyFile,
                url: `../${companyFile}`
            });
            
            // Track companies
            if (!this.companies.has(companyFile)) {
                this.companies.set(companyFile, {
                    name: companyName,
                    filename: companyFile,
                    url: `../${companyFile}`,
                    eventCodes: new Set()
                });
            }
            
            this.companies.get(companyFile).eventCodes.add(eventCodeName);
        });
        
        // Convert to arrays and sort
        this.filteredEventCodes = Array.from(this.eventCodes.values())
            .map(eventCode => ({
                ...eventCode,
                companies: Array.from(eventCode.companies.values()), // Convert Map values to Array
                companyCount: eventCode.companies.size
            }))
            .filter(eventCode => eventCode.companyCount > 0)
            .sort((a, b) => b.companyCount - a.companyCount);
        
        console.log('Top 5 event codes by company count:', 
            this.filteredEventCodes.slice(0, 5).map(e => `${e.name}: ${e.companyCount} companies`)
        );
    }
    
    displayEventCodes() {
        if (!this.eventCodeGrid) {
            console.error('Event code grid element not found');
            return;
        }
        
        if (this.filteredEventCodes.length === 0) {
            this.eventCodeGrid.innerHTML = `
                <div class="no-results">
                    <div class="no-results-content">
                        <div class="no-results-icon">📊</div>
                        <div class="no-results-text">
                            <strong>No event codes found</strong>
                            <p>Try adjusting your search terms</p>
                        </div>
                    </div>
                </div>
            `;
            return;
        }
        
        this.eventCodeGrid.innerHTML = this.filteredEventCodes
            .map(eventCode => this.createEventCodeCard(eventCode))
            .join('');
        
        // Store reference for global access
        window.eventCodeBrowser = this;
    }
    
    createEventCodeCard(eventCode) {
        const topCompanies = eventCode.companies
            .sort((a, b) => a.name.localeCompare(b.name))
            .slice(0, 5);
        
        return `
            <div class="event-code-category">
                <div class="event-code-header">
                    <h3>${eventCode.icon} ${eventCode.name}</h3>
                    <span class="company-count">${eventCode.companyCount} companies</span>
                </div>
                <div class="event-code-companies">
                    ${topCompanies.map(company => `
                        <a href="${company.url}" class="company-link">
                            <span class="company-name">${company.name}</span>
                        </a>
                    `).join('')}
                    ${eventCode.companyCount > 5 ? `
                        <div class="more-companies">
                            <span>+${eventCode.companyCount - 5} more companies</span>
                        </div>
                    ` : ''}
                </div>
                <div class="event-code-actions">
                    <button class="view-all-btn" onclick="eventCodeBrowser.showAllCompanies('${eventCode.name}')">
                        View All ${eventCode.companyCount} Companies
                    </button>
                </div>
            </div>
        `;
    }
    
    setupSearch() {
        if (!this.eventCodeSearch) {
            console.error('Event code search element not found');
            return;
        }
        
        let searchTimeout;
        this.eventCodeSearch.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.filterEventCodes(e.target.value);
            }, 300); // Debounce search
        });
    }
    
    filterEventCodes(searchTerm) {
        const term = searchTerm.toLowerCase().trim();
        
        if (term === '') {
            this.displayEventCodes();
            this.updateStats();
            return;
        }
        
        const filtered = this.filteredEventCodes.filter(eventCode =>
            eventCode.name.toLowerCase().includes(term) ||
            eventCode.companies.some(company => 
                company.name.toLowerCase().includes(term)
            )
        );
        
        // Temporarily update filteredEventCodes for display
        const originalFiltered = this.filteredEventCodes;
        this.filteredEventCodes = filtered;
        this.displayEventCodes();
        this.updateStats(searchTerm);
        this.filteredEventCodes = originalFiltered;
    }
    
    updateStats(searchTerm = '') {
        if (!this.eventCodeStats) return;
        
        const totalEventCodes = this.eventCodes.size;
        const displayedEventCodes = this.filteredEventCodes.length;
        const totalCompanies = this.companies.size;
        
        let statsText;
        if (searchTerm) {
            statsText = `${displayedEventCodes} of ${totalEventCodes} event codes found`;
        } else {
            statsText = `${totalEventCodes} event codes • ${totalCompanies} companies`;
        }
        
        this.eventCodeStats.innerHTML = `<span class="stat-badge">${statsText}</span>`;
    }
    
    formatCompanyName(filename) {
        let name = filename.replace('.html', '');
        
        // Handle specific company name cases first
        const specificCases = {
            'AARCORP': 'AAR Corp',
            'AAONINC': 'AAon Inc',
            'AAON': 'AAon',
            'AAR': 'AAR'
        };
        
        if (specificCases[name]) {
            return specificCases[name];
        }
        
        // Handle common company suffixes first
        name = name
            .replace(/INC$/, ' Inc')
            .replace(/CORP$/, ' Corp')
            .replace(/CO$/, ' Co')
            .replace(/LTD$/, ' Ltd')
            .replace(/LLC$/, ' LLC');
        
        // For all-caps names, we need a different approach
        // Split on common word boundaries and known patterns
        name = name
            .replace(/([A-Z])([A-Z][a-z])/g, '$1 $2')  // Handle cases like "ABCDef" -> "ABC Def"
            .replace(/([a-z])([A-Z])/g, '$1 $2')       // Handle cases like "abcDef" -> "abc Def"
            .trim();
        
        // If it's still all one word (all caps), try to split on known patterns
        if (!name.includes(' ') && name.length > 6) {
            // Try to identify common patterns
            name = name
                .replace(/LABORATORIES/g, ' Laboratories')
                .replace(/SYSTEMS/g, ' Systems')
                .replace(/TECHNOLOGIES/g, ' Technologies')
                .replace(/SOLUTIONS/g, ' Solutions')
                .replace(/SERVICES/g, ' Services')
                .replace(/INTERNATIONAL/g, ' International')
                .replace(/AMERICAN/g, 'American ')
                .replace(/GENERAL/g, 'General ')
                .replace(/NATIONAL/g, 'National ')
                .replace(/GLOBAL/g, 'Global ')
                .replace(/UNITED/g, 'United ')
                .trim();
        }
        
        const result = name.split(' ')
            .map(word => {
                if (word.length <= 2) return word.toUpperCase();
                return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
            })
            .join(' ');
        
        return result;
    }
    
    getEventCodeIcon(eventCodeName) {
        // Map event code names to appropriate icons
        const iconMap = {
            'vote': '🗳️',
            'solicit': '📢',
            'support': '🤝',
            'oppose': '❌',
            'lobby': '🏛️',
            'petition': '📝',
            'campaign': '🎯',
            'donate': '💰',
            'fund': '💵',
            'contribute': '🎁',
            'endorse': '✅',
            'recommend': '👍',
            'approve': '✔️',
            'reject': '❌',
            'propose': '💡',
            'submit': '📤',
            'file': '📁',
            'report': '📊',
            'disclose': '📋',
            'announce': '📣',
            'declare': '📢',
            'statement': '💬',
            'comment': '💭',
            'testimony': '🎤',
            'hearing': '👂',
            'meeting': '🤝',
            'conference': '🏢',
            'negotiate': '🤝',
            'agreement': '📄',
            'contract': '📋',
            'settlement': '⚖️',
            'lawsuit': '⚖️',
            'litigation': '⚖️',
            'compliance': '✅',
            'violation': '⚠️',
            'penalty': '💸',
            'fine': '💰'
        };
        
        const lowerName = eventCodeName.toLowerCase();
        for (const [key, icon] of Object.entries(iconMap)) {
            if (lowerName.includes(key)) {
                return icon;
            }
        }
        
        return '📊'; // Default icon
    }
    
    showAllCompanies(eventCodeName) {
        const eventCode = this.eventCodes.get(eventCodeName);
        if (!eventCode) return;
        
        const companies = Array.from(eventCode.companies.values())
            .sort((a, b) => a.name.localeCompare(b.name));
        
        const companyLinks = companies
            .map(company => `<a href="${company.url}" class="company-link">${company.name}</a>`)
            .join('');
        
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>${eventCode.icon} ${eventCodeName}</h2>
                    <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
                </div>
                <div class="modal-body">
                    <p><strong>${eventCode.companyCount} companies</strong> with this event code:</p>
                    <div class="company-grid">
                        ${companyLinks}
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Close modal when clicking outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }
    
    showError(message) {
        if (this.eventCodeGrid) {
            this.eventCodeGrid.innerHTML = `
                <div class="error-message">
                    <h3>⚠️ Error Loading Data</h3>
                    <p>${message}</p>
                    <button onclick="location.reload()" class="retry-btn">Retry</button>
                </div>
            `;
        }
        
        if (this.eventCodeStats) {
            this.eventCodeStats.innerHTML = '<span class="stat-badge error">Error loading data</span>';
        }
    }
}