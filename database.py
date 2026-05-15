import sqlite3
import random
from datetime import datetime

class Database:
    def __init__(self, db_name='rides.db'):
        self.db_name = db_name
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password TEXT,
            created_at TEXT
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS rides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_address TEXT,
            to_address TEXT,
            distance REAL,
            duration REAL,
            tariff TEXT,
            price REAL,
            weather TEXT,
            traffic TEXT,
            driver_name TEXT,
            car_model TEXT,
            driver_rating REAL,
            waiting_time INTEGER,
            created_at TEXT
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS drivers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            car_model TEXT,
            license_plate TEXT,
            tariff TEXT,
            rating REAL,
            lat REAL,
            lon REAL,
            is_online INTEGER DEFAULT 1,
            last_update TEXT
        )''')
        
        conn.commit()
        
        c.execute("SELECT COUNT(*) FROM drivers")
        if c.fetchone()[0] == 0:
            self._seed_drivers()
        
        conn.close()
    

    def register_user(self, email, password):
        import hashlib
        hashed = hashlib.sha256(password.encode()).hexdigest()
        
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute('INSERT INTO users (email, password, created_at) VALUES (?, ?, ?)',
                    (email, hashed, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False

    def login_user(self, email, password):
        import hashlib
        hashed = hashlib.sha256(password.encode()).hexdigest()
        
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('SELECT id, email FROM users WHERE email = ? AND password = ?', (email, hashed))
        user = c.fetchone()
        conn.close()
        
        if user:
            return {'id': user[0], 'email': user[1]}
        return None


    def _seed_drivers(self):
        driver_names = ['Александр Соколов', 'Дмитрий Кузнецов', 'Максим Попов', 
                       'Сергей Васильев', 'Андрей Петров', 'Владимир Смирнов',
                       'Иван Морозов', 'Михаил Волков', 'Николай Лебедев', 'Алексей Козлов']
        
        car_models = {
            'Fasten': ['Hyundai Solaris', 'Kia Rio', 'Renault Logan', 'Lada Vesta'],
            'Comfort': ['Toyota Corolla', 'Skoda Octavia', 'Hyundai Elantra', 'Kia Cerato'],
            'Comfort+': ['Toyota Camry', 'Volkswagen Passat', 'Mazda 6', 'Honda Accord'],
            'Business': ['Mercedes E-Class', 'BMW 5 Series', 'Audi A6', 'Lexus ES']
        }
        
        tariffs = ['Fasten', 'Comfort', 'Comfort+', 'Business']
        
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        
        center_lat, center_lon = 55.164441, 61.436843
        
        for i in range(20):
            tariff = random.choice(tariffs)
            name = driver_names[i % len(driver_names)]
            car_model = random.choice(car_models[tariff])
            rating = round(3.5 + random.random() * 1.5, 1)
            
            angle = random.random() * 2 * 3.14159
            distance = random.random() * 5000
            delta_lat = (distance / 111000) * angle
            delta_lon = (distance / (111000 * 0.5)) * angle
            
            c.execute('''INSERT INTO drivers 
                        (name, car_model, license_plate, tariff, rating, lat, lon, is_online, last_update)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (name, car_model, 
                       f"{chr(65+random.randint(0,25))}{random.randint(100,999)}{chr(65+random.randint(0,25))}{chr(65+random.randint(0,25))}",
                       tariff, rating, center_lat + delta_lat, center_lon + delta_lon, 1,
                       datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        conn.commit()
        conn.close()
    
    def get_drivers_by_tariff(self, tariff, limit=10):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('''SELECT id, name, car_model, license_plate, tariff, rating, lat, lon 
                    FROM drivers 
                    WHERE tariff = ? AND is_online = 1
                    ORDER BY rating DESC
                    LIMIT ?''', (tariff, limit))
        rows = c.fetchall()
        conn.close()
        
        drivers = []
        for row in rows:
            drivers.append({
                'id': row[0],
                'name': row[1],
                'car_model': row[2],
                'license_plate': row[3],
                'tariff': row[4],
                'rating': row[5],
                'lat': row[6],
                'lon': row[7]
            })
        return drivers
    
    def get_nearest_driver(self, pickup_lat, pickup_lon, tariff, calculator):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('''SELECT id, name, car_model, license_plate, tariff, rating, lat, lon 
                    FROM drivers 
                    WHERE tariff = ? AND is_online = 1''', (tariff,))
        rows = c.fetchall()
        conn.close()
        
        if not rows:
            return None
        
        nearest = None
        min_distance = float('inf')
        
        for row in rows:
            driver_lat = row[6]
            driver_lon = row[7]
            distance = calculator.calculate_distance_meters(pickup_lat, pickup_lon, driver_lat, driver_lon)
            
            if distance < min_distance:
                min_distance = distance
                nearest = {
                    'id': row[0],
                    'name': row[1],
                    'car_model': row[2],
                    'license_plate': row[3],
                    'tariff': row[4],
                    'rating': row[5],
                    'distance': round(distance, 0),
                    'waiting_time': round(distance / 500)
                }
        
        return nearest
    
    def update_driver_location(self, driver_id, lat, lon):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('''UPDATE drivers 
                    SET lat = ?, lon = ?, last_update = ?
                    WHERE id = ?''', 
                  (lat, lon, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), driver_id))
        conn.commit()
        conn.close()
    
    def save_ride(self, from_addr, to_addr, distance, duration, tariff, price, weather, traffic, driver_name, car_model, driver_rating, waiting_time):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('''INSERT INTO rides 
                    (from_address, to_address, distance, duration, tariff, price, weather, traffic, driver_name, car_model, driver_rating, waiting_time, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (from_addr, to_addr, distance, duration, tariff, price, weather, traffic, driver_name, car_model, driver_rating, waiting_time,
                   datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()

    def get_history(self, limit=50):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('''SELECT * FROM rides ORDER BY created_at DESC LIMIT ?''', (limit,))
        rows = c.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                'id': row[0],
                'from_address': row[1],
                'to_address': row[2],
                'distance': row[3],
                'duration': row[4],
                'tariff': row[5],
                'price': row[6],
                'weather': row[7],
                'traffic': row[8],
                'driver_name': row[9],
                'car_model': row[10],
                'driver_rating': row[11],
                'waiting_time': row[12],
                'created_at': row[13]
            })
        return history