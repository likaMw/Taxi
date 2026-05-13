document.addEventListener('DOMContentLoaded', function() {
    initMap();
    document.getElementById('infoTar').style.display = 'none';
    document.getElementById('infoCard').style.display = 'none';
});

let map;
let fromMarker;
let toMarker;
let routeLine;
let currentRouteData;
let carMarkers = [];

function initMap() {
    map = L.map('map').setView([55.164441, 61.436843], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);
}

async function findRoute() {
    carMarkers.forEach(marker => map.removeLayer(marker));
    carMarkers = [];

    const fromQuery = document.getElementById('fromInput').value;
    const toQuery = document.getElementById('toInput').value;
    
    if (!fromQuery || !toQuery) {
        alert('Введите адреса!');
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch('/api/calculate_route', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                from_address: fromQuery,
                to_address: toQuery
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            alert(data.error);
            return;
        }
        
        drawRoute([data.from_lat, data.from_lon], [data.to_lat, data.to_lon]);
        
        currentRouteData = data;
        
        document.getElementById('infoTar').style.display = 'block';
        
        // Обновляем цены в кнопках
        updateAllTariffPrices();
        updateTariffsWaitingTime(data.duration);
        
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Ошибка при построении маршрута');
    } finally {
        showLoading(false);
    }
}

function updateAllTariffPrices() {
    if (!currentRouteData) return;
    
    const tariffs = ['Fasten', 'Comfort', 'Comfort+', 'Business'];
    
    tariffs.forEach(tariff => {
        fetch('/api/calculate_final_price', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                distance: currentRouteData.distance,
                duration: currentRouteData.duration,
                tariff: tariff,
                weather_mult: currentRouteData.weather_mult,
                traffic_mult: currentRouteData.traffic_mult
            })
        })
        .then(response => response.json())
        .then(data => {
            const priceIds = {
                'Fasten': 'Fasten-price',
                'Comfort': 'Comfort-price',
                'Comfort+': 'Comfortplus-price',
                'Business': 'Business-price'
            };
            const priceSpan = document.getElementById(priceIds[tariff]);
            if (priceSpan) {
                priceSpan.textContent = data.price + ' ₽';
            }
        });
    });
}

function updateTariffsWaitingTime(duration) {
    const waitingTimes = {
        'Fasten': Math.round(duration * 0.8),
        'Comfort': Math.round(duration * 0.7),
        'Comfort+': Math.round(duration * 0.6),
        'Business': Math.round(duration * 0.5)
    };
    
    const waitingIds = {
        'Fasten': 'Fasten-duration-waiting',
        'Comfort': 'Comfort-duration-waiting',
        'Comfort+': 'Comfortplus-duration-waiting',
        'Business': 'Business-duration-waiting'
    };
    
    Object.entries(waitingTimes).forEach(([name, minutes]) => {
        const span = document.getElementById(waitingIds[name]);
        if (span) {
            span.textContent = minutes + ' мин';
        }
    });
}

async function orderRide() {
    if (!currentRouteData) {
        alert('Сначала постройте маршрут!');
        return;
    }
    
    const activeTariff = document.querySelector('.tariffs-btn.active');
    if (!activeTariff) {
        alert('Выберите тариф!');
        return;
    }
    
    const tariffName = activeTariff.querySelector('label').textContent;
    
    const driverResponse = await fetch('/api/get_nearest_driver', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            pickup_lat: currentRouteData.from_lat,
            pickup_lon: currentRouteData.from_lon,
            tariff: tariffName
        })
    });
    
    const driverData = await driverResponse.json();
    
    const response = await fetch('/api/calculate_final_price', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            distance: currentRouteData.distance,
            duration: currentRouteData.duration,
            tariff: tariffName,
            weather_mult: currentRouteData.weather_mult,
            traffic_mult: currentRouteData.traffic_mult
        })
    });
    
    const data = await response.json();
    
    document.getElementById('distance').innerHTML = currentRouteData.distance.toFixed(1) + ' км';
    document.getElementById('duration').innerHTML = Math.round(currentRouteData.duration) + ' мин';
    document.getElementById('price').innerHTML = data.price + ' ₽';
    document.getElementById('weather').innerHTML = currentRouteData.weather;
    document.getElementById('traffic').innerHTML = currentRouteData.traffic;
    document.getElementById('calculation').innerHTML = data.calculation;
    
    const driver = driverData.driver;
    let driverRow = document.getElementById('driver-row');
    if (!driverRow) {
        driverRow = document.createElement('div');
        driverRow.id = 'driver-row';
        driverRow.className = 'info-row';
        document.getElementById('infoCard').appendChild(driverRow);
    }
    driverRow.innerHTML = `<span>Водитель:</span><span>${driver.name} (${driver.car_model})<br><small>${driver.license_plate} ⭐ ${driver.rating}</small><br><small>🚗 Подача: ${driver.waiting_time} мин</small></span>`;
    
    document.getElementById('infoTar').style.display = 'none';
    document.getElementById('infoCard').style.display = 'block';
}

function drawRoute(fromCoord, toCoord) {
    if (fromMarker) map.removeLayer(fromMarker);
    if (toMarker) map.removeLayer(toMarker);
    if (routeLine) map.removeLayer(routeLine);
    
    const fromIcon = L.icon({
        iconUrl: 'img/fromCart.svg',
        iconSize: [20, 20],
        iconAnchor: [16, 32],
        popupAnchor: [0, -32]
    });

    const toIcon = L.icon({
        iconUrl: 'img/toCart.svg',
        className: 'toIcon',
        iconSize: [32, 32],
        iconAnchor: [16, 32],
        popupAnchor: [0, -32]
    });

    fromMarker = L.marker(fromCoord, {icon: fromIcon}).bindPopup('Отправление').addTo(map);
    toMarker = L.marker(toCoord, {icon: toIcon}).bindPopup('Назначение').addTo(map);
    
    routeLine = L.polyline([fromCoord, toCoord], {
        color: '#44ff33',
        weight: 4,
        opacity: 0.8
    }).addTo(map);
    
    const bounds = L.latLngBounds([fromCoord, toCoord]);
    map.fitBounds(bounds, { padding: [50, 50] });
}

function closeInfoCard() {
    document.getElementById('infoCard').style.display = 'none';
}

function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371000;
    const φ1 = lat1 * Math.PI / 180;
    const φ2 = lat2 * Math.PI / 180;
    const Δφ = (lat2 - lat1) * Math.PI / 180;
    const Δλ = (lon2 - lon1) * Math.PI / 180;
    
    const a = Math.sin(Δφ/2) * Math.sin(Δφ/2) +
              Math.cos(φ1) * Math.cos(φ2) *
              Math.sin(Δλ/2) * Math.sin(Δλ/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    
    return R * c;
}

function findNearestCar(lat, lon) {
    if (!carMarkers.length) return null;
    
    let nearest = null;
    let minDistance = Infinity;
    
    carMarkers.forEach(marker => {
        const markerLatLng = marker.getLatLng();
        const distance = calculateDistance(lat, lon, markerLatLng.lat, markerLatLng.lng);
        
        if (distance < minDistance) {
            minDistance = distance;
            nearest = { marker, distance };
        }
    });
    
    return nearest;
}

function updateWaitingTimeFromNearestCar(pickupLat, pickupLon, tariffName) {
    console.log('Ищем ближайшую машинку...');
    const nearest = findNearestCar(pickupLat, pickupLon);
    
    if (nearest) {
        const minutes = Math.ceil(nearest.distance / 500);
        console.log(`Ближайшая машинка на расстоянии ${Math.round(nearest.distance)}м, подача: ${minutes} мин`);
        
        const activeBtn = document.querySelector('.tariffs-btn.active');
        if (activeBtn) {
            const activeTariffName = activeBtn.querySelector('label').textContent;
            const waitingSpan = document.getElementById(`${activeTariffName}-duration-waiting`);
            if (waitingSpan) {
                waitingSpan.textContent = minutes + ' мин';
                console.log(`Обновлено время для ${activeTariffName}: ${minutes} мин`);
            } else {
                console.log(`Элемент ${activeTariffName}-duration-waiting не найден`);
            }
        }
    } else {
        console.log('Машинки не найдены');
    }
}

function addRandomCarsNearPoint(lat, lon, tariffName) {
    carMarkers.forEach(marker => {
        if (map && marker) map.removeLayer(marker);
    });
    carMarkers = [];
    
    const carCount = 8 + Math.floor(Math.random() * 5);
    
    const carIcons = {
        'Fasten': 'img/car-fasten.svg',
        'Comfort': 'img/car-comfort.svg',
        'Comfort+': 'img/car-comfortplus.svg',
        'Business': 'img/car-business.svg'
    };

    const carIcon = L.icon({
        iconUrl: carIcons[tariffName],
        iconSize: [32, 32],
        iconAnchor: [16, 16],
        popupAnchor: [0, -16],
        className: 'car-marker'
    });
    
    for (let i = 0; i < carCount; i++) {
        const angle = Math.random() * Math.PI * 2;
        const distance = 300 + Math.random() * 3000;
        const deltaLat = (distance / 111000) * Math.cos(angle);
        const deltaLon = (distance / (111000 * Math.cos(lat * Math.PI / 180))) * Math.sin(angle);
        
        const marker = L.marker([lat + deltaLat, lon + deltaLon], {icon: carIcon})
            .bindTooltip(tariffName, {permanent: false})
            .addTo(map);
        
        carMarkers.push(marker);
    }

    updateWaitingTimeFromNearestCar(lat, lon, tariffName);
}

function showLoading(show) {
    const loadingEl = document.getElementById('loading');
    if (loadingEl) loadingEl.style.display = show ? 'block' : 'none';
}

document.querySelectorAll('.tariffs-btn').forEach(btn => {
    const whySpan = btn.querySelector('.why-price');
    if (whySpan && !whySpan.textContent) {
        whySpan.textContent = 'Почему такая цена?';
    }
    
    btn.onclick = () => {
        document.querySelectorAll('.tariffs-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        document.querySelectorAll('.why-price').forEach(span => {
            span.style.display = 'none';
        });
        const activeSpan = btn.querySelector('.why-price');
        if (activeSpan) {
            activeSpan.style.display = 'block';
        }
        
        if (currentRouteData && currentRouteData.from_lat) {
            const tariffName = btn.querySelector('label')?.textContent || 'Fasten';
            addRandomCarsNearPoint(currentRouteData.from_lat, currentRouteData.from_lon, tariffName);

            setTimeout(() => {
                updateWaitingTimeFromNearestCar(currentRouteData.from_lat, currentRouteData.from_lon, tariffName);
            }, 100);
        }
    };
    
    if (whySpan) {
        whySpan.onclick = (e) => {
            e.stopPropagation();
            const tariffName = btn.querySelector('label')?.textContent || 'тариф';
            
            if (!currentRouteData) {
                alert('Сначала постройте маршрут!');
                return;
            }
            
            fetch('/api/calculate_final_price', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    distance: currentRouteData.distance,
                    duration: currentRouteData.duration,
                    tariff: tariffName,
                    weather_mult: currentRouteData.weather_mult,
                    traffic_mult: currentRouteData.traffic_mult
                })
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('price').innerHTML = data.price + ' ₽';
                document.getElementById('distance').innerHTML = currentRouteData.distance.toFixed(1) + ' км';
                document.getElementById('duration').innerHTML = Math.round(currentRouteData.duration) + ' мин';
                document.getElementById('weather').innerHTML = currentRouteData.weather;
                document.getElementById('traffic').innerHTML = currentRouteData.traffic;
                document.getElementById('calculation').innerHTML = data.calculation;
                
                fetch('/api/get_tariff_info', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ tariff: tariffName })
                })
                .then(response => response.json())
                .then(infoData => {
                    document.getElementById('tariffName').innerHTML = infoData.tariff_info;
                    document.getElementById('tariffExplanation').style.display = 'flex';
                    document.getElementById('priceExplanation').style.display = 'flex';
                    document.getElementById('calculation-detail').style.display = 'flex';
                    document.getElementById('infoCard').style.display = 'block';
                });
            })
            .catch(error => {
                console.error('Ошибка:', error);
                alert('Не удалось получить информацию');
            });
        };
    }
});

function closeTariffInfo() {
    document.getElementById('tariffExplanation').style.display = 'none';
    document.getElementById('priceExplanation').style.display = 'none';
    document.getElementById('infoCard').style.display = 'none';
}

document.addEventListener('click', function(event) {
    const infoCard = document.getElementById('infoCard');
    
    if (infoCard && infoCard.style.display === 'block') {
        const isClickInside = infoCard.contains(event.target);
        const isClickOnWhyPrice = event.target.classList?.contains('why-price') || 
                                  event.target.parentElement?.classList?.contains('why-price');
        
        if (!isClickInside && !isClickOnWhyPrice) {
            closeTariffInfo();
        }
    }
});

document.getElementById('btn-zakaz').onclick = orderRide;