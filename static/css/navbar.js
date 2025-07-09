document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('search-input');
    const suggestionsBox = document.getElementById('suggestions-box');
    const searchWrapper = document.getElementById('search-wrapper');

    searchInput.addEventListener('keyup', function () {
        const query = searchInput.value;

        if (query.length < 2) {
            suggestionsBox.style.display = 'none';
            return;
        }

        // Fetch suggestions from our Django view
        fetch(`{% url 'live_search_suggestions' %}?q=${query}`)
            .then(response => response.json())
            .then(data => {
                suggestionsBox.innerHTML = ''; // Clear old suggestions
                if (data.suggestions.length > 0) {
                    data.suggestions.forEach(item => {
                        const suggestionItem = document.createElement('a');
                        suggestionItem.href = item.url;
                        suggestionItem.classList.add('suggestion-item');
                        suggestionItem.innerHTML = `${item.title} <span class="item-type">${item.type}</span>`;
                        suggestionsBox.appendChild(suggestionItem);
                    });
                    suggestionsBox.style.display = 'block';
                } else {
                    suggestionsBox.style.display = 'none';
                }
            });
    });

    // Hide suggestions when clicking outside
    document.addEventListener('click', function (event) {
        if (!searchWrapper.contains(event.target)) {
            suggestionsBox.style.display = 'none';
        }
    });
});
