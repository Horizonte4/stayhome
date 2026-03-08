document.addEventListener('DOMContentLoaded', function () {
    const addressInput = document.getElementById('id_address');
    const cityInput = document.getElementById('id_city');
    const latInput = document.getElementById('id_latitude');
    const lngInput = document.getElementById('id_longitude');
    const resultsContainer = document.getElementById('location-results');
    const mapContainer = document.getElementById('property-map');

    if (!addressInput || !cityInput || !latInput || !lngInput || !resultsContainer || !mapContainer) {
        return;
    }

    const defaultLat = 4.7110;
    const defaultLng = -74.0721;

    const initialLat = parseFloat(latInput.value) || defaultLat;
    const initialLng = parseFloat(lngInput.value) || defaultLng;

    const map = L.map('property-map').setView([initialLat, initialLng], 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    const marker = L.marker([initialLat, initialLng], {
        draggable: true
    }).addTo(map);

    let debounceTimer = null;

    function showResults() {
        resultsContainer.style.display = 'block';
    }

    function hideResults() {
        resultsContainer.style.display = 'none';
        resultsContainer.innerHTML = '';
    }

    async function searchLocations(query) {
        const url = `https://nominatim.openstreetmap.org/search?format=json&addressdetails=1&limit=5&q=${encodeURIComponent(query)}`;

        const response = await fetch(url, {
            headers: {
                'Accept': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error('Error al buscar ubicaciones');
        }

        return await response.json();
    }

    async function reverseGeocode(lat, lng) {
        const url = `https://nominatim.openstreetmap.org/reverse?format=json&addressdetails=1&lat=${lat}&lon=${lng}`;

        const response = await fetch(url, {
            headers: {
                'Accept': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error('Error al obtener la dirección');
        }

        return await response.json();
    }

    function getCityFromAddress(addressData) {
        if (!addressData) return '';
        return (
            addressData.city ||
            addressData.town ||
            addressData.village ||
            addressData.municipality ||
            addressData.county ||
            ''
        );
    }

    function setSelectedLocation(displayName, city, lat, lng) {
        addressInput.value = displayName || '';
        cityInput.value = city || '';
        latInput.value = Number(lat).toFixed(6);
        lngInput.value = Number(lng).toFixed(6);

        marker.setLatLng([lat, lng]);
        map.setView([lat, lng], 16);
    }

    function renderResults(results) {
        resultsContainer.innerHTML = '';

        if (!results.length) {
            hideResults();
            return;
        }

        results.forEach(place => {
            const item = document.createElement('div');
            item.className = 'location-result-item';
            item.textContent = place.display_name;

            item.addEventListener('click', function () {
                const lat = parseFloat(place.lat);
                const lng = parseFloat(place.lon);
                const city = getCityFromAddress(place.address);

                setSelectedLocation(place.display_name, city, lat, lng);
                hideResults();
            });

            resultsContainer.appendChild(item);
        });

        showResults();
    }

    addressInput.addEventListener('input', function () {
        const query = this.value.trim();

        cityInput.value = '';
        latInput.value = '';
        lngInput.value = '';

        clearTimeout(debounceTimer);

        if (query.length < 3) {
            hideResults();
            return;
        }

        debounceTimer = setTimeout(async function () {
            try {
                const results = await searchLocations(query);
                renderResults(results);
            } catch (error) {
                console.error(error);
                hideResults();
            }
        }, 400);
    });

    marker.on('dragend', async function () {
        const position = marker.getLatLng();

        latInput.value = position.lat.toFixed(6);
        lngInput.value = position.lng.toFixed(6);

        try {
            const data = await reverseGeocode(position.lat, position.lng);
            const city = getCityFromAddress(data.address);

            addressInput.value = data.display_name || '';
            cityInput.value = city;
        } catch (error) {
            console.error(error);
        }
    });

    map.on('click', async function (event) {
        const lat = event.latlng.lat;
        const lng = event.latlng.lng;

        marker.setLatLng([lat, lng]);
        latInput.value = lat.toFixed(6);
        lngInput.value = lng.toFixed(6);

        try {
            const data = await reverseGeocode(lat, lng);
            const city = getCityFromAddress(data.address);

            addressInput.value = data.display_name || '';
            cityInput.value = city;
        } catch (error) {
            console.error(error);
        }
    });

    document.addEventListener('click', function (event) {
        const clickedInsideResults = resultsContainer.contains(event.target);
        const clickedAddressInput = addressInput.contains(event.target);

        if (!clickedInsideResults && !clickedAddressInput) {
            hideResults();
        }
    });

    setTimeout(function () {
        map.invalidateSize();
    }, 200);
});