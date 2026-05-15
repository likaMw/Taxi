import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from calculator import TaxiCalculator
from database import Database
import webbrowser
import threading

db = Database()
db.init_db()

class FastRideHandler(SimpleHTTPRequestHandler):
    
    def do_POST(self):
        length = int(self.headers['Content-Length'])
        data = json.loads(self.rfile.read(length))
        
        if self.path == '/api/register':
            email = data.get('email')
            password = data.get('password')
            
            if db.register_user(email, password):
                result = {'success': True, 'message': 'Регистрация успешна'}
            else:
                result = {'success': False, 'message': 'Пользователь уже существует'}

        elif self.path == '/api/login':
            email = data.get('email')
            password = data.get('password')
            
            user = db.login_user(email, password)
            if user:
                result = {'success': True, 'user': user}
            else:
                result = {'success': False, 'message': 'Неверная почта или пароль'}

        elif self.path == '/api/calculate_route':
            try:
                from_coord = TaxiCalculator.get_coordinates(data['from_address'])
                to_coord = TaxiCalculator.get_coordinates(data['to_address'])
                distance = TaxiCalculator.calculate_distance(from_coord[0], from_coord[1], to_coord[0], to_coord[1])
                
                weather, weather_mult = TaxiCalculator.get_weather_factor()
                traffic, traffic_mult = TaxiCalculator.get_traffic_factor()
                
                result = {
                    'from_lat': from_coord[0], 'from_lon': from_coord[1],
                    'to_lat': to_coord[0], 'to_lon': to_coord[1],
                    'distance': round(distance, 1),
                    'duration': round(distance * 2.5),
                    'weather': weather,
                    'weather_mult': weather_mult,
                    'traffic': traffic,
                    'traffic_mult': traffic_mult
                }
            except Exception as e:
                result = {'error': str(e)}
        
        elif self.path == '/api/get_weather_traffic':
            weather, weather_mult = TaxiCalculator.get_weather_factor()
            traffic, traffic_mult = TaxiCalculator.get_traffic_factor()
            
            result = {
                'weather': weather[0],
                'weather_text': weather,
                'weather_mult': weather_mult,
                'traffic': traffic[0],
                'traffic_text': traffic,
                'traffic_mult': traffic_mult
            }

        elif self.path == '/api/get_tariff_prices':
            result = {'prices': TaxiCalculator.get_tariff_prices(data['distance'], data['duration'])}
        
        elif self.path == '/api/get_tariff_info':
            tariff = data.get('tariff', '')
            info = TaxiCalculator.get_tariff_info(tariff)
            result = {
                'tariff_info': info['tariff_info'],
                'calculation': info['calculation']
            }

        elif self.path == '/api/calculate_final_price':
            calc = TaxiCalculator.calculate_final_price_with_factors(
                data['distance'], 
                data['duration'], 
                data['tariff'],
                data.get('weather_mult', 1.0),
                data.get('traffic_mult', 1.0)
            )
            
            result = {
                'price': calc['price'],
                'calculation': calc['calculation']
            }

        elif self.path == '/api/get_history':
            history = db.get_history()
            result = {'history': history}

        elif self.path == '/api/save_ride':
            db.save_ride(
                data.get('from_address', ''),
                data.get('to_address', ''),
                data['distance'],
                data['duration'],
                data['tariff'],
                data['price'],
                data.get('weather', ''),
                data.get('traffic', ''),
                data.get('driver_name', ''),
                data.get('car_model', ''),
                data.get('driver_rating', 0),
                data.get('waiting_time', 0)
            )
            result = {'success': True}
        
        elif self.path == '/api/get_rides_by_tariff':
            result = {'rides': db.get_rides_by_tariff(data['tariff'])}

        elif self.path == '/api/get_nearest_driver':
            pickup_lat = data.get('pickup_lat')
            pickup_lon = data.get('pickup_lon')
            tariff = data.get('tariff')
            
            nearest = db.get_nearest_driver(pickup_lat, pickup_lon, tariff, TaxiCalculator)
            if nearest:
                result = {'driver': nearest}
            else:
                result = {'error': 'Нет доступных водителей'}

        elif self.path == '/api/get_drivers_by_tariff':
            tariff = data.get('tariff')
            drivers = db.get_drivers_by_tariff(tariff)
            result = {'drivers': drivers}

        elif self.path == '/api/update_driver_location':
            driver_id = data.get('driver_id')
            lat = data.get('lat')
            lon = data.get('lon')
            db.update_driver_location(driver_id, lat, lon)
            result = {'success': True}

        else:
            self.send_response(404)
            self.end_headers()
            return
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())

print('✅ Сервер запущен: http://localhost:8000')
threading.Timer(1, lambda: webbrowser.open('http://localhost:8000')).start()
HTTPServer(('localhost', 8000), FastRideHandler).serve_forever()