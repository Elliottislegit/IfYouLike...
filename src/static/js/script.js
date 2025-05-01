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
        
        // Validate input
        const query = searchInput.value.trim();
        if (!query) {
            log.textContent = "Please enter a search term";
            return;
        }
        
        const mediaTypeInput = document.querySelector('input[name="media-type"]:checked');
        if (!mediaTypeInput) {
            log.textContent = "Please select a media type";
            return;
        }
        
        const mediaType = mediaTypeInput.value;
        
        // Show searching message with loading spinner
        log.innerHTML = `<span class="loading-text">Searching for ${mediaType}: "${query}"</span> <div class="loading-spinner"></div>`;
        
        // Show skeleton loading state while waiting
        showSkeletonLoaders();
        
        // Create the fetch request
        fetch('/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                type: mediaType
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Display the results
            displayResults(data.results);
            log.textContent = `Found ${data.results ? data.results.length : 0} results`;
        })
        .catch(error => {
            log.textContent = `Error: ${error}`;
            resultsContainer.innerHTML = '<div class="error-message">Sorry, there was a problem with your search. Please try again later.</div>';
            console.error('Search error:', error);
        });
    });
    
    // Show skeleton loaders while waiting for results
    function showSkeletonLoaders() {
        resultsContainer.innerHTML = '';
        const skeletonGrid = document.createElement('div');
        skeletonGrid.className = 'results-grid';
        
        // Create 6 skeleton cards
        for (let i = 0; i < 6; i++) {
            const skeletonCard = document.createElement('div');
            skeletonCard.className = 'result-card skeleton-card';
            skeletonCard.innerHTML = `
                <div class="skeleton skeleton-img"></div>
                <div class="result-info">
                    <div class="skeleton skeleton-title"></div>
                    <div class="skeleton skeleton-text"></div>
                    <div class="skeleton skeleton-btn"></div>
                </div>
            `;
            skeletonGrid.appendChild(skeletonCard);
        }
        
        resultsContainer.appendChild(skeletonGrid);
    }
    
    // Function to display search results
    function displayResults(results) {
        // Clear previous results
        resultsContainer.innerHTML = '';
        
        // Check if there are any results
        if (!results || results.length === 0) {
            resultsContainer.innerHTML = `
                <div class="no-results">
                    <div class="no-results-icon">🔍</div>
                    <p>No results found. Try a different search or check your spelling.</p>
                    <p class="no-results-suggestion">Try searching for a more popular ${document.querySelector('input[name="media-type"]:checked').value} title.</p>
                </div>`;
            return;
        }
        
        // Create results container
        const resultsGrid = document.createElement('div');
        resultsGrid.className = 'results-grid';
        
        // Add each result as a card
        results.forEach(item => {
            const card = document.createElement('div');
            card.className = 'result-card';
            
            // Format year display
            const yearDisplay = item.year && item.year !== 'Unknown' ? `(${item.year})` : '';
            
            // Create placeholder for missing images
            const imageUrl = item.image_url || '/static/images/placeholder.png';
            
            // Add badge for media type
            const typeBadge = `<span class="type-badge ${item.type}-badge">${item.type}</span>`;
            
            card.innerHTML = `
                <div class="card-header">
                    ${typeBadge}
                </div>
                <img src="${imageUrl}" alt="${item.title}" onerror="this.src='/static/images/placeholder.png'">
                <div class="result-info">
                    <h3>${item.title}</h3>
                    <p class="creator">${item.creator} ${yearDisplay}</p>
                    <button class="select-btn" data-id="${item.id}">Get Recommendations</button>
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
                log.innerHTML = `<span class="loading-text">Finding perfect matches</span> <div class="loading-spinner"></div>`;
                
                // Show recommendation skeletons while waiting
                showRecommendationSkeletons();
                
                // Request recommendations for this item
                fetch('/get_recommendations', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        item_id: selectedId
                    })
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    // Display recommendations
                    displayRecommendations(data.selected_item, data.recommendations);
                    log.textContent = `Found ${data.recommendations.length} recommendations based on your selection`;
                })
                .catch(error => {
                    log.textContent = `Error: ${error}`;
                    resultsContainer.innerHTML = '<div class="error-message">Sorry, there was a problem getting recommendations. Please try again later.</div>';
                    console.error('Recommendation error:', error);
                });
            });
        });
    }
    
    // Show recommendation skeleton loaders
    function showRecommendationSkeletons() {
        resultsContainer.innerHTML = '';
        
        // Selected item skeleton
        const selectedSkeleton = document.createElement('div');
        selectedSkeleton.className = 'selected-item skeleton-selected';
        selectedSkeleton.innerHTML = `
            <h3>Based on your selection:</h3>
            <div class="selected-card">
                <div class="skeleton skeleton-img-large"></div>
                <div class="selected-info">
                    <div class="skeleton skeleton-title-large"></div>
                    <div class="skeleton skeleton-text"></div>
                    <div class="skeleton skeleton-text-long"></div>
                </div>
            </div>
        `;
        
        // Recommendations skeleton
        const recsSkeleton = document.createElement('div');
        recsSkeleton.className = 'recommendations-section';
        recsSkeleton.innerHTML = '<h3>Finding recommendations...</h3>';
        
        const recsGrid = document.createElement('div');
        recsGrid.className = 'recommendations-grid';
        
        // Create 3 skeleton cards
        for (let i = 0; i < 3; i++) {
            const skeletonCard = document.createElement('div');
            skeletonCard.className = 'recommendation-card skeleton-card';
            skeletonCard.innerHTML = `
                <div class="skeleton skeleton-img"></div>
                <div class="rec-info">
                    <div class="skeleton skeleton-title"></div>
                    <div class="skeleton skeleton-badge"></div>
                    <div class="skeleton skeleton-text"></div>
                    <div class="skeleton skeleton-text-short"></div>
                    <div class="skeleton skeleton-btn"></div>
                </div>
            `;
            recsGrid.appendChild(skeletonCard);
        }
        
        recsSkeleton.appendChild(recsGrid);
        resultsContainer.appendChild(selectedSkeleton);
        resultsContainer.appendChild(recsSkeleton);
    }
    
    // Function to display recommendations
    function displayRecommendations(selectedItem, recommendations) {
        // Clear previous results
        resultsContainer.innerHTML = '';
        
        // Create selected item section
        const selectedSection = document.createElement('div');
        selectedSection.className = 'selected-item';
        
        // Format year display
        const yearDisplay = selectedItem.year && selectedItem.year !== 'Unknown' ? `(${selectedItem.year})` : '';
        
        // Create placeholder for missing images
        const imageUrl = selectedItem.image_url || '/static/images/placeholder.png';
        
        // Add media type badge
        const typeBadge = `<span class="type-badge ${selectedItem.type}-badge">${selectedItem.type}</span>`;
        
        selectedSection.innerHTML = `
            <h3>Based on your selection:</h3>
            <div class="selected-card">
                <div class="selected-image-container">
                    <img src="${imageUrl}" alt="${selectedItem.title}" onerror="this.src='/static/images/placeholder.png'">
                    ${typeBadge}
                </div>
                <div class="selected-info">
                    <h2>${selectedItem.title}</h2>
                    <p class="creator">${selectedItem.creator} ${yearDisplay}</p>
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
        
        // Check if there are any recommendations
        if (!recommendations || recommendations.length === 0) {
            recsGrid.innerHTML = '<div class="no-results"><p>No recommendations found for this selection.</p></div>';
        } else {
            // Add each recommendation
            recommendations.forEach(rec => {
                const item = rec.item;
                const card = document.createElement('div');
                card.className = 'recommendation-card';
                
                // Format year display
                const recYearDisplay = item.year && item.year !== 'Unknown' ? `(${item.year})` : '';
                
                // Create placeholder for missing images
                const recImageUrl = item.image_url || '/static/images/placeholder.png';
                
                // Add media type badge - highlight if different from selected item
                const isDifferentType = item.type !== selectedItem.type;
                const recTypeBadge = `<span class="type-badge ${item.type}-badge ${isDifferentType ? 'highlight-badge' : ''}">${item.type}</span>`;
                
                card.innerHTML = `
                    <div class="rec-card-header">
                        ${recTypeBadge}
                    </div>
                    <img src="${recImageUrl}" alt="${item.title}" onerror="this.src='/static/images/placeholder.png'">
                    <div class="rec-info">
                        <h3>${item.title}</h3>
                        <p class="creator">${item.creator} ${recYearDisplay}</p>
                        <p class="relationship">${rec.relationship_type}</p>
                        <button class="select-btn" data-id="${item.id}">Select This Instead</button>
                    </div>
                `;
                
                recsGrid.appendChild(card);
            });
        }
        
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
                log.innerHTML = `<span class="loading-text">Finding new recommendations</span> <div class="loading-spinner"></div>`;
                
                // Show recommendation skeletons while waiting
                showRecommendationSkeletons();
                
                // Request recommendations for this new item
                fetch('/get_recommendations', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        item_id: selectedId
                    })
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    // Display new recommendations
                    displayRecommendations(data.selected_item, data.recommendations);
                    log.textContent = `Found ${data.recommendations.length} new recommendations`;
                })
                .catch(error => {
                    log.textContent = `Error: ${error}`;
                    console.error('Recommendation error:', error);
                });
            });
        });
    }
});