// Exposure Browser JavaScript
class ExposureBrowser {
    constructor() {
        this.searchData = [];
        this.exposures = new Map();
        this.companies = new Map();
        this.filteredExposures = [];
        
        this.exposureGrid = document.getElementById('exposureGrid');
        this.exposureStats = document.getElementById('exposureStats');
        this.exposureSearch = document.getElementById('exposureSearch');
        
        this.init();
    }
    
    async init() {
        try {
            console.log('Initializing exposure browser...');
            await this.loadData();
            console.log(`Loaded ${this.searchData.length} search entries`);
            this.processExposures();
            console.log(`Processed ${this.exposures.size} exposures`);
            this.displayExposures();
            this.setupSearch();
            this.updateStats();
        } catch (error) {
            console.error('Failed to initialize exposure browser:', error);
            this.showError(`Failed to load exposure data: ${error.message}`);
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
    
    processExposures() {
        // Filter for exposure entries only
        const exposureEntries = this.searchData.filter(item => item.type === 'Exposure');
        console.log(`Found ${exposureEntries.length} exposure entries`);
        
        // Group companies by exposure
        exposureEntries.forEach(entry => {
            const exposureName = entry.title;
            const companyFile = entry.source_file;
            const companyName = this.formatCompanyName(companyFile);
            
            // Track exposures
            if (!this.exposures.has(exposureName)) {
                this.exposures.set(exposureName, {
                    name: exposureName,
                    companies: new Map(), // Use Map instead of Set
                    icon: this.getExposureIcon(exposureName)
                });
            }
            
            // Add company to exposure (Map will handle duplicates by filename)
            this.exposures.get(exposureName).companies.set(companyFile, {
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
                    exposures: new Set()
                });
            }
            
            this.companies.get(companyFile).exposures.add(exposureName);
        });
        
        // Convert to arrays and sort
        this.filteredExposures = Array.from(this.exposures.values())
            .map(exposure => ({
                ...exposure,
                companies: Array.from(exposure.companies.values()), // Convert Map values to Array
                companyCount: exposure.companies.size
            }))
            .filter(exposure => exposure.companyCount > 0)
            .sort((a, b) => b.companyCount - a.companyCount);
        
        console.log('Top 5 exposures by company count:', 
            this.filteredExposures.slice(0, 5).map(e => `${e.name}: ${e.companyCount} companies`)
        );
    }
    
    displayExposures() {
        if (!this.exposureGrid) {
            console.error('Exposure grid element not found');
            return;
        }
        
        if (this.filteredExposures.length === 0) {
            this.exposureGrid.innerHTML = `
                <div class="no-results">
                    <div class="no-results-content">
                        <div class="no-results-icon">🎯</div>
                        <div class="no-results-text">
                            <strong>No exposures found</strong>
                            <p>Try adjusting your search terms</p>
                        </div>
                    </div>
                </div>
            `;
            return;
        }
        
        this.exposureGrid.innerHTML = this.filteredExposures
            .map(exposure => this.createExposureCard(exposure))
            .join('');
        
        // Store reference for global access
        window.exposureBrowser = this;
    }
    
    createExposureCard(exposure) {
        const topCompanies = exposure.companies
            .sort((a, b) => a.name.localeCompare(b.name))
            .slice(0, 5);
        
        return `
            <div class="exposure-category">
                <div class="exposure-header">
                    <h3>${exposure.icon} ${exposure.name}</h3>
                    <span class="company-count">${exposure.companyCount} companies</span>
                </div>
                <div class="exposure-companies">
                    ${topCompanies.map(company => `
                        <a href="${company.url}" class="company-link">
                            <span class="company-name">${company.name}</span>
                        </a>
                    `).join('')}
                    ${exposure.companyCount > 5 ? `
                        <div class="more-companies">
                            <span>+${exposure.companyCount - 5} more companies</span>
                        </div>
                    ` : ''}
                </div>
                <div class="exposure-actions">
                    <button class="view-all-btn" onclick="exposureBrowser.showAllCompanies('${exposure.name}')">
                        View All ${exposure.companyCount} Companies
                    </button>
                </div>
            </div>
        `;
    }
    
    setupSearch() {
        if (!this.exposureSearch) {
            console.error('Exposure search element not found');
            return;
        }
        
        let searchTimeout;
        this.exposureSearch.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.filterExposures(e.target.value);
            }, 300); // Debounce search
        });
    }
    
    filterExposures(searchTerm) {
        const term = searchTerm.toLowerCase().trim();
        
        if (term === '') {
            this.displayExposures();
            this.updateStats();
            return;
        }
        
        const filtered = this.filteredExposures.filter(exposure =>
            exposure.name.toLowerCase().includes(term) ||
            exposure.companies.some(company => 
                company.name.toLowerCase().includes(term)
            )
        );
        
        // Temporarily update filteredExposures for display
        const originalFiltered = this.filteredExposures;
        this.filteredExposures = filtered;
        this.displayExposures();
        this.updateStats(searchTerm);
        this.filteredExposures = originalFiltered;
    }
    
    updateStats(searchTerm = '') {
        if (!this.exposureStats) return;
        
        const totalExposures = this.exposures.size;
        const displayedExposures = this.filteredExposures.length;
        const totalCompanies = this.companies.size;
        
        let statsText;
        if (searchTerm) {
            statsText = `${displayedExposures} of ${totalExposures} exposures found`;
        } else {
            statsText = `${totalExposures} exposures • ${totalCompanies} companies`;
        }
        
        this.exposureStats.innerHTML = `<span class="stat-badge">${statsText}</span>`;
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
    
    getExposureIcon(exposureName) {
        // Map exposure names to appropriate icons
        const iconMap = {
            'military': '🪖',
            'leadership': '👔',
            'government': '🏛️',
            'political': '🗳️',
            'regulatory': '📋',
            'legal': '⚖️',
            'financial': '💰',
            'economic': '📈',
            'environmental': '🌍',
            'social': '👥',
            'technology': '💻',
            'cyber': '🔒',
            'security': '🛡️',
            'operational': '⚙️',
            'strategic': '🎯',
            'reputational': '📢',
            'compliance': '✅',
            'market': '📊',
            'credit': '💳',
            'liquidity': '💧'
        };
        
        const lowerName = exposureName.toLowerCase();
        for (const [key, icon] of Object.entries(iconMap)) {
            if (lowerName.includes(key)) {
                return icon;
            }
        }
        
        return '🎯'; // Default icon
    }
    
    showAllCompanies(exposureName) {
        const exposure = this.exposures.get(exposureName);
        if (!exposure) return;
        
        const companies = Array.from(exposure.companies.values())
            .sort((a, b) => a.name.localeCompare(b.name));
        
        const companyLinks = companies
            .map(company => `<a href="${company.url}" class="company-link">${company.name}</a>`)
            .join('');
        
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>${exposure.icon} ${exposureName}</h2>
                    <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
                </div>
                <div class="modal-body">
                    <p><strong>${exposure.companyCount} companies</strong> with this exposure:</p>
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
        if (this.exposureGrid) {
            this.exposureGrid.innerHTML = `
                <div class="error-message">
                    <h3>⚠️ Error Loading Data</h3>
                    <p>${message}</p>
                    <button onclick="location.reload()" class="retry-btn">Retry</button>
                </div>
            `;
        }
        
        if (this.exposureStats) {
            this.exposureStats.innerHTML = '<span class="stat-badge error">Error loading data</span>';
        }
    }
}