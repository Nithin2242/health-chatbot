import sqlite3

def setup_database():
    # This creates a file named 'healthcare.db' in your folder
    conn = sqlite3.connect('healthcare.db')
    cursor = conn.cursor()
    
    # Create the doctors table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_name TEXT,
            specialty TEXT,
            hospital_clinic TEXT,
            location TEXT,
            contact_number TEXT
        )
    ''')
    
    # Clear out any old data if you run this script multiple times
    cursor.execute('DELETE FROM doctors')
    
    # Insert premium mock data based on real Bangalore medical centers
    doctors_data = [
        ('Dr. Ramesh Kumar', 'Orthopedics', 'HOSMAT Hospital', 'Ashok Nagar', '080-12345670'),
        ('Dr. Sneha Reddy', 'Dietetics & Nutrition', 'Sakra World Hospital', 'Bellandur', '080-12345671'),
        ('Dr. Anil Sharma', 'General Medicine', 'Aster CMI Hospital', 'Hebbal', '080-12345672'),
        ('Dr. Priya Desai', 'Orthopedics', 'Manipal Hospital', 'Old Airport Road', '080-12345673'),
        ('Dr. Vikram Singh', 'Sports Medicine', 'Fortis Hospital', 'Bannerghatta Road', '080-12345674'),
        ('Dr. Kavita Menon', 'Clinical Nutrition', 'Vasavi Hospitals', 'Kumaraswamy Layout', '080-12345675')
    ]
    
    cursor.executemany('''
        INSERT INTO doctors (doctor_name, specialty, hospital_clinic, location, contact_number)
        VALUES (?, ?, ?, ?, ?)
    ''', doctors_data)
    
    # Save the changes and close the connection
    conn.commit()
    conn.close()
    print("✅ Database 'healthcare.db' created successfully with Bangalore mock data!")

if __name__ == "__main__":
    setup_database()