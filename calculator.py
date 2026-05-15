import math
import random
import urllib.request
import urllib.parse
import json
import ssl
import time
from functools import lru_cache

ssl._create_default_https_context = ssl._create_unverified_context

class TaxiCalculator:
    
    @staticmethod
    def get_coordinates(address):
        YANDEX_API_KEY = "ddac7a1a-846f-4dcc-813d-241a0bd6dbd6"
        
        try:
            encoded = urllib.parse.quote(address)
            url = f"https://geocode-maps.yandex.ru/1.x/?apikey={YANDEX_API_KEY}&geocode={encoded}&format=json"
            
            req = urllib.request.Request(url, headers={'User-Agent': 'FastRideApp/1.0'})
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
            
            geo_objects = data['response']['GeoObjectCollection']['featureMember']
            if geo_objects:
                coords = geo_objects[0]['GeoObject']['Point']['pos'].split()
                lon, lat = float(coords[0]), float(coords[1])
                return [lat, lon]
            else:
                return [55.164441, 61.436843]
                
        except Exception as e:
            return TaxiCalculator._search_fallback(address)
    
    @staticmethod
    def _search_fallback(address):
        try:
            encoded = urllib.parse.quote(address.encode('utf-8'))
            url = f"https://nominatim.openstreetmap.org/search?q={encoded}&format=json&limit=1&accept-language=ru"
            
            req = urllib.request.Request(url, headers={'User-Agent': 'FastRideApp/1.0'})
            time.sleep(1)
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
            
            if data and len(data) > 0:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                return [lat, lon]
            else:
                return [55.164441, 61.436843]
                
        except Exception as e:
            return [55.164441, 61.436843]
    
    @staticmethod
    def calculate_distance(lat1, lon1, lat2, lon2):
        R = 6371
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return R * c
    
    @staticmethod
    def get_tariff_prices(distance, duration):
        prices = {
            'Fasten': round(50 + distance * 15 + duration * 5),
            'Comfort': round(80 + distance * 20 + duration * 7),
            'Comfort+': round(120 + distance * 28 + duration * 10),
            'Business': round(200 + distance * 40 + duration * 15)
        }
        return prices
    
    @staticmethod
    def get_weather_factor():
        weathers = [('☀️ Солнечно', 1.0), ('🌧️ Дождь', 1.2), ('❄️ Снег', 1.3), ('🌫️ Туман', 1.1)]
        return random.choice(weathers)
    
    @staticmethod
    def get_traffic_factor():
        traffics = [('🟢 Свободно', 1.0), ('🟡 Средне', 1.15), ('🔴 Плотно', 1.3), ('🔴 Стоим', 1.5)]
        return random.choice(traffics)
    
    @staticmethod
    def calculate_final_price_with_factors(distance, duration, tariff, weather_mult, traffic_mult):
        prices = TaxiCalculator.get_tariff_prices(distance, duration)
        base_price = prices.get(tariff, 0)
        
        tariff_mult = {'Fasten': 1.0, 'Comfort': 1.3, 'Comfort+': 1.6, 'Business': 2.0}.get(tariff, 1.0)
        
        final_price = base_price * weather_mult * traffic_mult * tariff_mult
        
        return {
            'price': round(final_price),
            'calculation': f"{base_price}₽ (база) × {tariff_mult} (тариф) × {weather_mult} (погода) × {traffic_mult} (пробки) = {round(final_price)}₽"
        }
    
    @staticmethod
    def get_tariff_info(tariff_name):
        info = {
            'Fasten': '🚀 Эконом. Быстрая подача, авто эконом-класса до 5 лет. Коэффициент ×1.0',
            'Comfort': '🚗 Комфорт. Просторный салон, кондиционер, водитель в форме. Коэффициент ×1.3',
            'Comfort+': '✨ Комфорт+. Автомобили бизнес-класса, кожаный салон. Коэффициент ×1.6',
            'Business': '💼 Бизнес. Премиум авто, высший сервис. Коэффициент ×2.0'
        }
        formulas = {
            'Fasten': '50₽ посадка + 15₽/км + 5₽/мин',
            'Comfort': '80₽ посадка + 20₽/км + 7₽/мин',
            'Comfort+': '120₽ посадка + 28₽/км + 10₽/мин',
            'Business': '200₽ посадка + 40₽/км + 15₽/мин'
        }
        return {
            'tariff_info': info.get(tariff_name, 'Информация недоступна'),
            'calculation': formulas.get(tariff_name, 'Расчет недоступен')
        }
    
    @staticmethod
    def calculate_final_price(distance, duration, tariff):
        prices = TaxiCalculator.get_tariff_prices(distance, duration)
        base_price = prices.get(tariff, 0)
        weather, weather_mult = TaxiCalculator.get_weather_factor()
        traffic, traffic_mult = TaxiCalculator.get_traffic_factor()
        
        tariff_mult = {'Fasten': 1.0, 'Comfort': 1.3, 'Comfort+': 1.6, 'Business': 2.0}.get(tariff, 1.0)
        
        final_price = base_price * weather_mult * traffic_mult * tariff_mult
        
        return {
            'price': round(final_price),
            'weather': weather,
            'weather_mult': weather_mult,
            'traffic': traffic,
            'traffic_mult': traffic_mult,
            'calculation': f"{base_price}₽ (база) × {tariff_mult} (тариф) × {weather_mult} (погода) × {traffic_mult} (пробки) = {round(final_price)}₽"
        }
    
    @staticmethod
    def calculate_distance_meters(lat1, lon1, lat2, lon2):
        R = 6371000
        φ1 = lat1 * math.pi / 180
        φ2 = lat2 * math.pi / 180
        Δφ = (lat2 - lat1) * math.pi / 180
        Δλ = (lon2 - lon1) * math.pi / 180
        
        a = math.sin(Δφ/2)**2 + math.cos(φ1) * math.cos(φ2) * math.sin(Δλ/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c