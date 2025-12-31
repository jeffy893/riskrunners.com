// Main JavaScript for Risk Runners
class RiskRunnersApp {
    constructor() {
        this.init();
    }
    
    init() {
        this.setupAnimations();
        this.setupLazyLoading();
        this.setupSmoothScrolling();
        this.setupVideoOptimization();
        this.setupAccessibility();
    }
    
    setupAnimations() {
        // Intersection Observer for fade-in animations
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in');
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);
        
        // Observe elements for animation
        const animateElements = document.querySelectorAll(
            '.info-section, .search-container, .stats-section, .browse-section, .featured-section'
        );
        
        animateElements.forEach(el => {
            observer.observe(el);
        });
    }
    
    setupLazyLoading() {
        // Lazy load images and iframes
        const lazyElements = document.querySelectorAll('img[data-src], iframe[data-src]');
        
        if ('IntersectionObserver' in window) {
            const lazyObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const element = entry.target;
                        element.src = element.dataset.src;
                        element.classList.remove('lazy');
                        lazyObserver.unobserve(element);
                    }
                });
            });
            
            lazyElements.forEach(el => {
                el.classList.add('lazy');
                lazyObserver.observe(el);
            });
        } else {
            // Fallback for older browsers
            lazyElements.forEach(el => {
                el.src = el.dataset.src;
            });
        }
    }
    
    setupSmoothScrolling() {
        // Enhanced smooth scrolling for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                
                if (target) {
                    const headerOffset = 80;
                    const elementPosition = target.getBoundingClientRect().top;
                    const offsetPosition = elementPosition + window.pageYOffset - headerOffset;
                    
                    window.scrollTo({
                        top: offsetPosition,
                        behavior: 'smooth'
                    });
                }
            });
        });
    }
    
    setupVideoOptimization() {
        const video = document.querySelector('iframe[src*="youtube"]');
        if (video) {
            // Add loading="lazy" for better performance
            video.setAttribute('loading', 'lazy');
            
            // Optimize for mobile
            if (window.innerWidth < 768) {
                video.style.height = '250px';
            }
        }
    }
    
    setupAccessibility() {
        // Skip to main content link
        this.addSkipLink();
        
        // Keyboard navigation improvements
        this.improveKeyboardNavigation();
        
        // ARIA labels and descriptions
        this.enhanceARIA();
    }
    
    addSkipLink() {
        const skipLink = document.createElement('a');
        skipLink.href = '#main-content';
        skipLink.textContent = 'Skip to main content';
        skipLink.className = 'skip-link';
        skipLink.style.cssText = `
            position: absolute;
            top: -40px;
            left: 6px;
            background: var(--primary-color);
            color: white;
            padding: 8px;
            text-decoration: none;
            border-radius: 4px;
            z-index: 1000;
            transition: top 0.3s;
        `;
        
        skipLink.addEventListener('focus', () => {
            skipLink.style.top = '6px';
        });
        
        skipLink.addEventListener('blur', () => {
            skipLink.style.top = '-40px';
        });
        
        document.body.insertBefore(skipLink, document.body.firstChild);
        
        // Add id to main content
        const main = document.querySelector('main');
        if (main) {
            main.id = 'main-content';
            main.setAttribute('tabindex', '-1');
        }
    }
    
    improveKeyboardNavigation() {
        // Add focus indicators for interactive elements
        const focusableElements = document.querySelectorAll(
            'a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        
        focusableElements.forEach(el => {
            el.addEventListener('focus', () => {
                el.classList.add('keyboard-focus');
            });
            
            el.addEventListener('blur', () => {
                el.classList.remove('keyboard-focus');
            });
        });
    }
    
    enhanceARIA() {
        // Add ARIA labels to search
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.setAttribute('aria-label', 'Search companies and risk factors');
            searchInput.setAttribute('aria-describedby', 'search-help');
            
            // Add search help text
            const helpText = document.createElement('div');
            helpText.id = 'search-help';
            helpText.className = 'sr-only';
            helpText.textContent = 'Search by company name, ticker symbol, industry, or risk factor. Use filters to narrow results.';
            searchInput.parentNode.appendChild(helpText);
        }
        
        // Add ARIA labels to filter buttons
        document.querySelectorAll('.filter-btn').forEach(btn => {
            const filter = btn.dataset.filter;
            btn.setAttribute('aria-label', `Filter by ${filter}`);
            btn.setAttribute('role', 'button');
        });
        
        // Add ARIA labels to stats
        document.querySelectorAll('.stat-item').forEach(stat => {
            const number = stat.querySelector('.stat-number');
            const label = stat.querySelector('.stat-label');
            if (number && label) {
                stat.setAttribute('aria-label', `${number.textContent} ${label.textContent}`);
            }
        });
    }
}

// Performance monitoring
class PerformanceMonitor {
    constructor() {
        this.metrics = {};
        this.init();
    }
    
    init() {
        if ('performance' in window) {
            this.measurePageLoad();
            this.measureSearchPerformance();
        }
    }
    
    measurePageLoad() {
        window.addEventListener('load', () => {
            setTimeout(() => {
                const perfData = performance.getEntriesByType('navigation')[0];
                if (perfData) {
                    this.metrics.pageLoad = {
                        domContentLoaded: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
                        loadComplete: perfData.loadEventEnd - perfData.loadEventStart,
                        totalTime: perfData.loadEventEnd - perfData.fetchStart
                    };
                    
                    console.log('Page Performance:', this.metrics.pageLoad);
                }
            }, 0);
        });
    }
    
    measureSearchPerformance() {
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            let searchStartTime;
            
            searchInput.addEventListener('input', () => {
                searchStartTime = performance.now();
            });
            
            // Monitor search results display
            const observer = new MutationObserver(() => {
                if (searchStartTime) {
                    const searchEndTime = performance.now();
                    const searchTime = searchEndTime - searchStartTime;
                    
                    if (searchTime > 100) {
                        console.log(`Search took ${searchTime.toFixed(2)}ms`);
                    }
                    
                    searchStartTime = null;
                }
            });
            
            const searchResults = document.getElementById('searchResults');
            if (searchResults) {
                observer.observe(searchResults, { childList: true });
            }
        }
    }
}

// Error handling
window.addEventListener('error', (e) => {
    console.error('JavaScript Error:', e.error);
    
    // Show user-friendly error message for critical failures
    if (e.error && e.error.message.includes('search')) {
        const searchContainer = document.querySelector('.search-container');
        if (searchContainer) {
            const errorMsg = document.createElement('div');
            errorMsg.className = 'error-message';
            errorMsg.innerHTML = `
                <p>⚠️ Search functionality is temporarily unavailable. Please try refreshing the page.</p>
            `;
            searchContainer.appendChild(errorMsg);
        }
    }
});

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new RiskRunnersApp();
    new PerformanceMonitor();
    
    // Add loading states
    document.body.classList.add('loaded');
});

// Service Worker registration for offline support
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => {
                console.log('SW registered: ', registration);
            })
            .catch(registrationError => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}