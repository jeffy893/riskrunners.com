// Industry Browser JavaScript
class IndustryBrowser {
    constructor() {
        this.searchData = [];
        this.industries = new Map();
        this.companies = new Map();
        this.filteredIndustries = [];
        
        this.industryGrid = document.getElementById('industryGrid');
        this.industryStats = document.getElementById('industryStats');
        this.industrySearch = document.getElementById('industrySearch');
        
        this.init();
    }
    
    async init() {
        try {
            console.log('Initializing industry browser...');
            await this.loadData();
            console.log(`Loaded ${this.searchData.length} search entries`);
            this.processIndustries();
            console.log(`Processed ${this.industries.size} industries`);
            this.displayIndustries();
            this.setupSearch();
            this.updateStats();
        } catch (error) {
            console.error('Failed to initialize industry browser:', error);
            this.showError(`Failed to load industry data: ${error.message}`);
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
        
        // If we get here, all paths failed
        console.error('Failed to load search data from all attempted paths');
        console.error('Current location:', window.location.href);
        console.error('Last error:', lastError);
        throw new Error(`Failed to load search index. Last error: ${lastError?.message || 'Unknown error'}`);
    }
    
    processIndustries() {
        // Filter for industry entries only
        const industryEntries = this.searchData.filter(item => item.type === 'Industry');
        console.log(`Found ${industryEntries.length} industry entries`);
        
        // Group companies by industry
        industryEntries.forEach(entry => {
            const industryName = entry.title;
            const companyFile = entry.source_file;
            const companyName = this.formatCompanyName(companyFile);
            
            // Track industries
            if (!this.industries.has(industryName)) {
                this.industries.set(industryName, {
                    name: industryName,
                    companies: new Map(), // Use Map instead of Set
                    icon: this.getIndustryIcon(industryName)
                });
            }
            
            // Add company to industry (Map will handle duplicates by filename)
            this.industries.get(industryName).companies.set(companyFile, {
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
                    industries: new Set()
                });
            }
            
            this.companies.get(companyFile).industries.add(industryName);
        });
        
        // Convert to arrays and sort
        this.filteredIndustries = Array.from(this.industries.values())
            .map(industry => ({
                ...industry,
                companies: Array.from(industry.companies.values()), // Convert Map values to Array
                companyCount: industry.companies.size
            }))
            .filter(industry => industry.companyCount > 0)
            .sort((a, b) => b.companyCount - a.companyCount);
        
        console.log('Top 5 industries by company count:', 
            this.filteredIndustries.slice(0, 5).map(e => `${e.name}: ${e.companyCount} companies`)
        );
    }
    
    displayIndustries() {
        if (!this.industryGrid) {
            console.error('Industry grid element not found');
            return;
        }
        
        if (this.filteredIndustries.length === 0) {
            this.industryGrid.innerHTML = `
                <div class="no-results">
                    <div class="no-results-content">
                        <div class="no-results-icon">🏭</div>
                        <div class="no-results-text">
                            <strong>No industries found</strong>
                            <p>Try adjusting your search terms</p>
                        </div>
                    </div>
                </div>
            `;
            return;
        }
        
        this.industryGrid.innerHTML = this.filteredIndustries
            .map(industry => this.createIndustryCard(industry))
            .join('');
        
        // Store reference for global access
        window.industryBrowser = this;
    }
    
    createIndustryCard(industry) {
        const topCompanies = industry.companies
            .sort((a, b) => a.name.localeCompare(b.name))
            .slice(0, 5);
        
        return `
            <div class="industry-category">
                <div class="industry-header">
                    <h3>${industry.icon} ${industry.name}</h3>
                    <span class="company-count">${industry.companyCount} companies</span>
                </div>
                <div class="industry-companies">
                    ${topCompanies.map(company => `
                        <a href="${company.url}" class="company-link">
                            <span class="company-name">${company.name}</span>
                        </a>
                    `).join('')}
                    ${industry.companyCount > 5 ? `
                        <div class="more-companies">
                            <span>+${industry.companyCount - 5} more companies</span>
                        </div>
                    ` : ''}
                </div>
                <div class="industry-actions">
                    <button class="view-all-btn" onclick="industryBrowser.showAllCompanies('${industry.name}')">
                        View All ${industry.companyCount} Companies
                    </button>
                </div>
            </div>
        `;
    }
    
    showAllCompanies(industryName) {
        const industry = this.industries.get(industryName);
        if (!industry) return;
        
        const companies = Array.from(industry.companies.values())
            .sort((a, b) => a.name.localeCompare(b.name));
        
        const companyLinks = companies
            .map(company => `<a href="${company.url}" class="company-link">${company.name}</a>`)
            .join('');
        
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>${industry.icon} ${industryName}</h2>
                    <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
                </div>
                <div class="modal-body">
                    <p><strong>${industry.companyCount} companies</strong> in this industry:</p>
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
    
    setupSearch() {
        if (!this.industrySearch) return;
        
        this.industrySearch.addEventListener('input', (e) => {
            const query = e.target.value.trim().toLowerCase();
            
            if (query.length === 0) {
                this.filteredIndustries = Array.from(this.industries.values())
                    .map(industry => ({
                        ...industry,
                        companies: Array.from(industry.companies.values()),
                        companyCount: industry.companies.size
                    }))
                    .filter(industry => industry.companyCount > 0)
                    .sort((a, b) => b.companyCount - a.companyCount);
            } else {
                this.filteredIndustries = Array.from(this.industries.values())
                    .filter(industry => 
                        industry.name.toLowerCase().includes(query) ||
                        Array.from(industry.companies.values()).some(company => 
                            company.name.toLowerCase().includes(query)
                        )
                    )
                    .map(industry => ({
                        ...industry,
                        companies: Array.from(industry.companies.values()),
                        companyCount: industry.companies.size
                    }))
                    .sort((a, b) => b.companyCount - a.companyCount);
            }
            
            this.displayIndustries();
            this.updateStats();
        });
    }
    
    updateStats() {
        if (!this.industryStats) return;
        
        const totalIndustries = this.industries.size;
        const totalCompanies = this.companies.size;
        const filteredIndustries = this.filteredIndustries.length;
        
        this.industryStats.innerHTML = `
            <span class="stat-badge">${totalIndustries} Industries</span>
            <span class="stat-badge">${totalCompanies} Companies</span>
            ${filteredIndustries !== totalIndustries ? 
                `<span class="stat-badge">${filteredIndustries} Filtered</span>` : ''
            }
        `;
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
    
    getIndustryIcon(industryName) {
        const iconMap = {
            'Technology': '💻',
            'Software': '💻',
            'Hardware': '🔧',
            'Healthcare': '🏥',
            'Pharmaceuticals': '💊',
            'Biotechnology': '🧬',
            'Financial': '🏦',
            'Banking': '🏦',
            'Insurance': '🛡️',
            'Energy': '⚡',
            'Oil': '🛢️',
            'Gas': '⛽',
            'Manufacturing': '🏭',
            'Automotive': '🚗',
            'Aerospace': '✈️',
            'Consumer': '🛒',
            'Retail': '🛍️',
            'Food': '🍽️',
            'Real Estate': '🏢',
            'Transportation': '🚛',
            'Telecommunications': '📡',
            'Media': '📺',
            'Entertainment': '🎬'
        };
        
        for (const [key, icon] of Object.entries(iconMap)) {
            if (industryName.toLowerCase().includes(key.toLowerCase())) {
                return icon;
            }
        }
        
        return '🏢'; // Default icon
    }
    
    showError(message) {
        this.industryGrid.innerHTML = `
            <div class="search-error">
                <div class="error-content">
                    <span class="error-icon">⚠️</span>
                    <span class="error-message">${message}</span>
                </div>
            </div>
        `;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.industryBrowser = new IndustryBrowser();
});