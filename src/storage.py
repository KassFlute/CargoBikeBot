import csv
import threading
import uuid
from datetime import datetime
import os

dirname = os.path.dirname(__file__)

class ReservationStorage:
    def __init__(self, filename=os.path.join(dirname,'../storage/reservations.csv')):
        self.filename = filename
        self.lock = threading.Lock()
        self._initialize_csv()

    def _initialize_csv(self):
        """Initialize the CSV file with a header if it doesn't exist."""
        with self.lock:
            try:
                with open(self.filename, 'x', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['reservation_id', 'user_id', 'username', 'first_name', 'last_name', 'association_name', 'email', 'bike_id', 'start_datetime', 'end_datetime', 'status'])
            except FileExistsError:
                pass

    def add_reservation(self, user_id:int, username:str, first_name:str, last_name:str, association_name:str, email:str, bike_id:int, start_datetime:datetime, end_datetime:datetime, status:str='pending'):
        """Add a new reservation to the CSV file."""
        reservation_id = int(uuid.uuid4().int >> 64)  # Convert UUID to a unique integer
        with self.lock:
            with open(self.filename, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([reservation_id, user_id, username, first_name, last_name, association_name, email, bike_id, start_datetime, end_datetime, status])

    def get_reservation_by_id(self, reservation_id):
        """Retrieve a reservation by its ID, converting ID to int."""
        with self.lock:
            with open(self.filename, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if int(row['reservation_id']) == reservation_id:  # Convert CSV ID to int for comparison
                        row['reservation_id'] = int(row['reservation_id'])  # Convert ID field back to int
                        row['user_id'] = int(row['user_id'])
                        row['bike_id'] = int(row['bike_id'])
                        return row
        return None

    def list_reservations(self):
        """List all reservations, converting IDs to int."""
        with self.lock:
            reservations = []
            with open(self.filename, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    row['reservation_id'] = int(row['reservation_id'])
                    row['user_id'] = int(row['user_id'])
                    row['bike_id'] = int(row['bike_id'])
                    row['start_datetime'] = datetime.strptime(row['start_datetime'], '%Y-%m-%d %H:%M:%S')
                    row['end_datetime'] = datetime.strptime(row['end_datetime'], '%Y-%m-%d %H:%M:%S')
                    reservations.append(row)
            return reservations

    def list_reservations_for_user(self, user_id):
        """List all reservations for a specific user, converting IDs to int."""
        with self.lock:
            user_reservations = []
            with open(self.filename, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if int(row['user_id']) == user_id:  # Convert CSV ID to int for comparison
                        row['reservation_id'] = int(row['reservation_id'])
                        row['user_id'] = int(row['user_id'])
                        row['bike_id'] = int(row['bike_id'])
                        row['start_datetime'] = datetime.strptime(row['start_datetime'], '%Y-%m-%d %H:%M:%S')
                        row['end_datetime'] = datetime.strptime(row['end_datetime'], '%Y-%m-%d %H:%M:%S')
                        user_reservations.append(row)
            return user_reservations


class BikeStorage:
    def __init__(self, filename=os.path.join(dirname,'../storage/bikes.csv')):
        self.filename = filename
        self.lock = threading.Lock()
        self._initialize_csv()

    def _initialize_csv(self):
        """Initialize the CSV file with a header if it doesn't exist."""
        with self.lock:
            try:
                with open(self.filename, 'x', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['bike_id', 'size', 'name'])
            except FileExistsError:
                pass

    def add_bike(self, bike_id, size, name):
        """Add a new bike to the CSV file, ensuring bike_id is int."""
        with self.lock:
            with open(self.filename, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([int(bike_id), size, name])

    def get_bike_by_id(self, bike_id):
        """Retrieve a bike by its ID, ensuring IDs are treated as int."""
        with self.lock:
            with open(self.filename, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if int(row['bike_id']) == bike_id:  # Convert CSV ID to int for comparison
                        row['bike_id'] = int(row['bike_id'])
                        return row
        return None

    def list_bikes(self):
        """List all bikes, converting IDs to int."""
        with self.lock:
            bikes = []
            with open(self.filename, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    row['bike_id'] = int(row['bike_id'])
                    bikes.append(row)
            return bikes

class UserStorage:
    def __init__(self, filename=os.path.join(dirname,'../storage/users.csv')):
        self.filename = filename
        self.lock = threading.Lock()
        self._initialize_csv()
        
    def _initialize_csv(self):
        """Initialize the CSV file with a header if it doesn't exist."""
        with self.lock:
            try:
                with open(self.filename, 'x', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['user_id', 'username', 'first_name', 'last_name', 'association', 'email'])
            except FileExistsError:
                pass
            
    def add_user(self, user_id:int, username:str, first_name:str, last_name:str, association:str, email:str):
        """Add a new user to the CSV file."""
        with self.lock:
            with open(self.filename, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([user_id, username, first_name, last_name, association, email])
        
    def update_user(self, user_id:int, username:str, first_name:str, last_name:str, association:str, email:str):
        """Update an existing user in the CSV file."""
        with self.lock:
            with open(self.filename, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                rows = list(reader)
            with open(self.filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['user_id', 'username', 'first_name', 'last_name', 'association_name', 'email'])
                for row in rows:
                    if int(row['user_id']) == user_id:
                        writer.writerow([user_id, username, first_name, last_name, association, email])
                    else:
                        writer.writerow(int(row['user_id']), row['username'], row['first_name'], row['last_name'], row['association_name'], row['email'])       
                
    def get_user_by_id(self, user_id):
        """Retrieve a user by its ID, converting ID to int."""
        with self.lock:
            with open(self.filename, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if int(row['user_id']) == user_id:
                        row['user_id'] = int(row['user_id'])
                        return row
        return None
    
    def list_users(self):
        """List all users, converting IDs to int."""
        with self.lock:
            users = []
            with open(self.filename, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    row['user_id'] = int(row['user_id'])
                    users.append(row)
            return users
