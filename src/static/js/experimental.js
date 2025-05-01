// This is a copy of the original script.js with the endpoint URLs changed
// to point to the experimental endpoints

document.addEventListener('DOMContentLoaded', function() {
    // Get form and elements
    const form = document.getElementById("search-form");
    const log = document.getElementById("log");
    const searchInput = document.getElementById("search-input");
    const resultsContainer = document.getElementById("search-results");
    
    // Add submit event listener
    form.addEventListener("submit", function(event) {
        // Prevent default form submission
        event.preventDefault();
        
        // Get the search query and media type
        const query = searchInput.value;
        const mediaType = document.querySelector('input[name="media-type"]:checked').value;
        
        // Show searching message with loading spinner
        log.innerHTML = `<span class="loading-text">Searching for ${mediaType}: "${query}"</span> <div class="loading-spinner"></div>`;
        
        // Create the fetch request
        fetch('/experimental/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                type: mediaType
            })
        })
        .then(response => response.json())
        .then(data => {
            // Display the results
            displayResults(data.results);
            log.textContent = `Found ${data.results ? data.results.length : 0} results`;
        })
        .catch(error => {
            log.textContent = `Error: ${error}`;
            console.error('Search error:', error);
        });
    });
    
    // Function to display search results
    function displayResults(results) {
        // Clear previous results
        resultsContainer.innerHTML = '';
        
        // Check if there are any results
        if (!results || results.length === 0) {
            resultsContainer.innerHTML = '<div class="no-results"><p>No results found. Try a different search.</p></div>';
            return;
        }
        
        // Create results container
        const resultsGrid = document.createElement('div');
        resultsGrid.className = 'results-grid';
        
        // Add each result as a card
        results.forEach(item => {
            const card = document.createElement('div');
            card.className = 'result-card';
            
            card.innerHTML = `
                <img src="${item.image_url}" alt="${item.title}">
                <div class="result-info">
                    <h3>${item.title}</h3>
                    <p>${item.creator} (${item.year})</p>
                    <button class="select-btn" data-id="${item.id}">Select This</button>
                </div>
            `;
            
            resultsGrid.appendChild(card);
        });
        
        // Add the results grid to the container
        resultsContainer.appendChild(resultsGrid);
        
        // Add event listeners to the select buttons
        document.querySelectorAll('.select-btn').forEach(button => {
            button.addEventListener('click', function() {
                const selectedId = this.getAttribute('data-id');
                log.innerHTML = `<span class="loading-text">Generating recommendations</span> <div class="loading-spinner"></div>`;
                
                // Request recommendations for this item
                fetch('/experimental/get_recommendations', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        item_id: selectedId
                    })
                })
                .then(response => response.json())
                .then(data => {
                    // Display recommendations
                    displayRecommendations(data.selected_item, data.recommendations);
                    log.textContent = `Found ${data.recommendations.length} recommendations`;
                })
                .catch(error => {
                    log.textContent = `Error: ${error}`;
                    console.error('Recommendation error:', error);
                });
            });
        });
    }
    
    // Function to display recommendations
    function displayRecommendations(selectedItem, recommendations) {
        // Clear previous results
        resultsContainer.innerHTML = '';
        
        // Create selected item section
        const selectedSection = document.createElement('div');
        selectedSection.className = 'selected-item';
        selectedSection.innerHTML = `
            <h3>Based on your selection:</h3>
            <div class="selected-card">
                <img src="${selectedItem.image_url}" alt="${selectedItem.title}">
                <div class="selected-info">
                    <h2>${selectedItem.title}</h2>
                    <p class="creator">${selectedItem.creator} (${selectedItem.year})</p>
                    <p class="description">${selectedItem.description || 'No description available.'}</p>
                </div>
            </div>
        `;
        
        // Create recommendations section
        const recsSection = document.createElement('div');
        recsSection.className = 'recommendations-section';
        
        // Add heading
        const recsHeading = document.createElement('h3');
        recsHeading.textContent = 'You might also like:';
        recsSection.appendChild(recsHeading);
        
        // Create recommendations grid
        const recsGrid = document.createElement('div');
        recsGrid.className = 'recommendations-grid';
        
        // Add each recommendation
        recommendations.forEach(rec => {
            const item = rec.item;
            const card = document.createElement('div');
            card.className = 'recommendation-card';
            
            card.innerHTML = `
                <img src="${item.image_url}" alt="${item.title}">
                <div class="rec-info">
                    <h3>${item.title}</h3>
                    <p class="type-badge">${item.type}</p>
                    <p class="creator">${item.creator} (${item.year})</p>
                    <p class="relationship">${rec.relationship_type}</p>
                    <button class="select-btn" data-id="${item.id}">Select This Instead</button>
                </div>
            `;
            
            recsGrid.appendChild(card);
        });
        
        // Add back button
        const backButton = document.createElement('button');
        backButton.className = 'back-button';
        backButton.textContent = 'Back to Search';
        backButton.addEventListener('click', function() {
            // Clear results and go back to search
            resultsContainer.innerHTML = '';
            log.textContent = '';
        });
        
        // Add everything to the results container
        recsSection.appendChild(recsGrid);
        resultsContainer.appendChild(selectedSection);
        resultsContainer.appendChild(recsSection);
        resultsContainer.appendChild(backButton);
        
        // Add event listeners to the new select buttons
        document.querySelectorAll('.recommendation-card .select-btn').forEach(button => {
            button.addEventListener('click', function() {
                const selectedId = this.getAttribute('data-id');
                log.innerHTML = `<span class="loading-text">Generating new recommendations</span> <div class="loading-spinner"></div>`;
                
                // Request recommendations for this new item
                fetch('/experimental/get_recommendations', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        item_id: selectedId
                    })
                })
                .then(response => response.json())
                .then(data => {
                    // Display new recommendations
                    displayRecommendations(data.selected_item, data.recommendations);
                    log.textContent = `Found ${data.recommendations.length} recommendations`;
                })
                .catch(error => {
                    log.textContent = `Error: ${error}`;
                    console.error('Recommendation error:', error);
                });
            });
        });
    }
});