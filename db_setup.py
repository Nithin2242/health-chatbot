import sqlite3

def setup_database():
    conn = sqlite3.connect('healthcare.db')
    cursor = conn.cursor()
    
    # Drop the old table so we can safely rebuild it with the new 'city' column
    cursor.execute('DROP TABLE IF EXISTS doctors')
    
    # Create the updated table
    cursor.execute('''
        CREATE TABLE doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_name TEXT,
            specialty TEXT,
            hospital_clinic TEXT,
            location TEXT,
            city TEXT,
            contact_number TEXT
        )
    ''')
    
    # Premium mock data based on real top-tier hospitals
    doctors_data = [
        # Bangalore
        ('Dr. Ramesh Kumar', 'Orthopedics', 'HOSMAT Hospital', 'Ashok Nagar', 'Bangalore', '080-12345670'),
        ('Dr. Sneha Reddy', 'Dietetics & Nutrition', 'Sakra World Hospital', 'Bellandur', 'Bangalore', '080-12345671'),
        ('Dr. Anil Sharma', 'General Medicine', 'Aster CMI Hospital', 'Hebbal', 'Bangalore', '080-12345672'),
        
        # Mumbai
        ('Dr. Vikram Desai', 'Cardiology', 'SR Mehta & Kika Bhai Hospital', 'Mumbai Central', 'Mumbai', '022-12345673'),
        ('Dr. Priya Singh', 'General Medicine', 'Lilavati Hospital', 'Bandra West', 'Mumbai', '022-12345674'),
        ('Dr. Rohan Mehta', 'Oncology', 'Kokilaben Hospital', 'Andheri West', 'Mumbai', '022-12345675'),
        
        # Delhi
        ('Dr. Sanjay Gupta', 'Orthopedics', 'AIIMS', 'Ansari Nagar', 'Delhi', '011-12345676'),
        ('Dr. Neha Sharma', 'Cardiology', 'Fortis Hospital', 'Vasant Kunj', 'Delhi', '011-12345677'),
        ('Dr. Amit Verma', 'General Medicine', 'Sir Ganga Ram Hospital', 'Rajendra Nagar', 'Delhi', '011-12345678'),
        
        # Chennai
        ('Dr. Lakshmi Iyer', 'General Medicine', 'Apollo Hospital', 'Greams Road', 'Chennai', '044-12345679'),
        ('Dr. Karthik Raj', 'Orthopedics', 'MGM Healthcare', 'Aminjikarai', 'Chennai', '044-12345680'),
        ('Dr. Anjali Menon', 'Neurology', 'Gleneagles Global Health City', 'Perumbakkam', 'Chennai', '044-12345681')
    ]
    
    cursor.executemany('''
        INSERT INTO doctors (doctor_name, specialty, hospital_clinic, location, city, contact_number)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', doctors_data)
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    setup_database()
