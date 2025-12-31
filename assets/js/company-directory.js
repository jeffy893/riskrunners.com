// Company Directory JavaScript
class CompanyDirectory {
    constructor() {
        this.companies = [];
        this.filteredCompanies = [];
        this.fuse = null;
        this.searchInput = document.getElementById('companySearch');
        this.companyGrid = document.getElementById('companyGrid');
        this.totalCount = document.getElementById('totalCount');
        this.filteredCount = document.getElementById('filteredCount');
        
        this.init();
    }
    
    async init() {
        try {
            console.log('Initializing company directory...');
            await this.loadCompanies();
            console.log(`Loaded ${this.companies.length} companies`);
            this.setupSearch();
            this.displayCompanies(this.companies);
            this.updateStats();
        } catch (error) {
            console.error('Failed to initialize company directory:', error);
            this.showError(`Failed to load company directory: ${error.message}`);
        }
    }
    
    async loadCompanies() {
        // Try multiple possible paths for the search index
        const possiblePaths = [
            '../data/002_search-index.json',
            './data/002_search-index.json',
            '/data/002_search-index.json',
            'data/002_search-index.json'
        ];
        
        let lastError = null;
        
        for (const path of possiblePaths) {
            try {
                console.log('Attempting to load search index from:', path);
                const response = await fetch(path);
                
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
                
                const searchData = JSON.parse(text);
                console.log(`Successfully parsed ${searchData.length} search entries from ${path}`);
                
                // Extract unique companies from search data
                const companyMap = new Map();
                
                searchData.forEach(item => {
                    const filename = item.source_file;
                    if (filename && filename.endsWith('.html')) {
                        const companyName = this.formatCompanyName(filename);
                        
                        if (!companyMap.has(filename)) {
                            companyMap.set(filename, {
                                name: companyName,
                                filename: filename,
                                url: `../${filename}`, // Correct path from /companies/ to root
                                industries: new Set(),
                                exposures: new Set(),
                                eventCodes: new Set()
                            });
                        }
                        
                        const company = companyMap.get(filename);
                        
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
                    }
                });
                
                // Convert to array and sort
                this.companies = Array.from(companyMap.values())
                    .map(company => ({
                        ...company,
                        industries: Array.from(company.industries),
                        exposures: Array.from(company.exposures),
                        eventCodes: Array.from(company.eventCodes)
                    }))
                    .sort((a, b) => a.name.localeCompare(b.name));
                
                this.filteredCompanies = [...this.companies];
                
                console.log(`Processed ${this.companies.length} unique companies`);
                
                // Setup Fuse.js for search if available
                if (typeof Fuse !== 'undefined') {
                    const fuseOptions = {
                        keys: ['name', 'industries', 'exposures'],
                        threshold: 0.3,
                        includeScore: true
                    };
                    
                    this.fuse = new Fuse(this.companies, fuseOptions);
                    console.log('Fuse.js search initialized');
                } else {
                    console.warn('Fuse.js not available, using basic search');
                    this.fuse = null;
                }
                
                return; // Success, exit the function
                
            } catch (error) {
                console.warn(`Failed to load from ${path}:`, error.message);
                lastError = error;
                continue; // Try next path
            }
        }
        
        // If we get here, all paths failed
        console.error('Failed to load companies from all attempted paths');
        console.error('Last error:', lastError);
        throw new Error(`Failed to load search index. Last error: ${lastError?.message || 'Unknown error'}`);
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
        
        // Capitalize first letter of each word
        return name.split(' ')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
            .join(' ');
    }
    
    setupSearch() {
        if (!this.searchInput) return;
        
        this.searchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();
            
            if (query.length === 0) {
                this.filteredCompanies = [...this.companies];
            } else if (query.length >= 2) {
                if (this.fuse) {
                    // Use Fuse.js if available
                    const results = this.fuse.search(query);
                    this.filteredCompanies = results.map(result => result.item);
                } else {
                    // Fallback to basic search
                    this.filteredCompanies = this.companies.filter(company => 
                        company.name.toLowerCase().includes(query.toLowerCase()) ||
                        company.industries.some(industry => 
                            industry.toLowerCase().includes(query.toLowerCase())
                        )
                    );
                }
            }
            
            this.displayCompanies(this.filteredCompanies);
            this.updateStats();
        });
    }
    
    displayCompanies(companies) {
        if (companies.length === 0) {
            this.companyGrid.innerHTML = `
                <div class="no-results">
                    <div class="no-results-content">
                        <div class="no-results-icon">🔍</div>
                        <div class="no-results-text">
                            <strong>No companies found</strong>
                            <p>Try adjusting your search terms</p>
                        </div>
                    </div>
                </div>
            `;
            return;
        }
        
        this.companyGrid.innerHTML = companies
            .map(company => this.createCompanyCard(company))
            .join('');
    }
    
    createCompanyCard(company) {
        const primaryIndustry = company.industries[0] || 'Various Industries';
        const riskCount = company.exposures.length + company.eventCodes.length;
        
        return `
            <div class="company-item">
                <a href="${company.url}" class="company-link">
                    <h4>${company.name}</h4>
                    <p class="company-industry">${primaryIndustry}</p>
                    <div class="company-stats">
                        <span class="stat-item">
                            <span class="stat-icon">🏭</span>
                            ${company.industries.length} Industries
                        </span>
                        <span class="stat-item">
                            <span class="stat-icon">⚠️</span>
                            ${riskCount} Risk Factors
                        </span>
                    </div>
                </a>
            </div>
        `;
    }
    
    updateStats() {
        this.totalCount.textContent = `${this.companies.length} Total Companies`;
        
        if (this.filteredCompanies.length !== this.companies.length) {
            this.filteredCount.textContent = `${this.filteredCompanies.length} Filtered`;
            this.filteredCount.style.display = 'inline-block';
        } else {
            this.filteredCount.style.display = 'none';
        }
    }
    
    showError(message) {
        this.companyGrid.innerHTML = `
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
    new CompanyDirectory();
});