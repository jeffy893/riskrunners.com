document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    const searchResults = document.getElementById('searchResults');
    let fuse; // To hold our Fuse.js instance
    const MAX_DISPLAY_RESULTS = 50; // Limit the number of results shown

    // Fetch the search index
    fetch('/002_search-index.json')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(indexData => {
            // Configure Fuse.js - SEARCH ONLY IN 'title' (the link node string)
            const fuseOptions = {
                keys: ['title'],
                threshold: 0.3, // Adjust fuzzy matching sensitivity
                // You might need to play with threshold for better results on node strings
            };
            fuse = new Fuse(indexData, fuseOptions);
            console.log("Search index loaded successfully.");
            console.log(`Indexed unique link nodes: ${indexData.length}`);
        })
        .catch(error => {
            console.error('Error loading search index:', error);
            searchResults.innerHTML = '<li>Error loading search index. Please try again later.</li>';
            searchResults.style.display = 'block';
        });

    // Listen for input in the search bar
    searchInput.addEventListener('input', (event) => {
        event.preventDefault(); // Prevent default action

        const query = event.target.value.trim();

        if (query.length === 0) {
            searchResults.innerHTML = '';
            searchResults.style.display = 'none'; // Hide results when empty
            return;
        }

        searchResults.style.display = 'block';

        if (fuse) {
            const results = fuse.search(query);
            console.log(`Search for "${query}" found ${results.length} results.`);

            searchResults.innerHTML = '';
            if (results.length > 0) {
                results.slice(0, MAX_DISPLAY_RESULTS).forEach(result => {
                    const item = result.item;
                    const li = document.createElement('li');
                    const a = document.createElement('a');

                    // The URL links to the file where the node was found
                    a.href = item.url;
                    // Display the node string (title)
                    a.textContent = item.title;
                    li.appendChild(a);

                    // Add context: Type and Source File
                    const p = document.createElement('p');
                    p.textContent = `${item.type} | Source: ${item.source_file}`;
                    p.style.fontSize = '12px';
                    p.style.color = '#666';
                    p.style.marginTop = '2px';

                    li.appendChild(p);

                    searchResults.appendChild(li);
                });

                 if (results.length > MAX_DISPLAY_RESULTS) {
                      const moreInfo = document.createElement('li');
                      moreInfo.textContent = `(${results.length - MAX_DISPLAY_RESULTS} more results - refine search)`;
                      moreInfo.style.fontStyle = 'italic';
                      moreInfo.style.fontSize = '12px';
                      moreInfo.style.color = '#666';
                      searchResults.appendChild(moreInfo);
                 }

            } else {
                searchResults.innerHTML = '<li>No results found.</li>';
            }
        } else {
            searchResults.innerHTML = '<li>Loading search index...</li>';
        }
    });

     searchInput.addEventListener('search', () => {
         if (searchInput.value === '') {
             searchResults.innerHTML = '';
             searchResults.style.display = 'none';
         }
     });

     // Hide results initially
     searchResults.style.display = 'none';
});