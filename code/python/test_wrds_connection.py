import os
import dotenv
import wrds

def load_wrds_credentials():
    '''
    Load WRDS credentials from secrets.env file.
    '''
    if os.path.exists('secrets.env'):
        dotenv.load_dotenv('secrets.env')
        wrds_username = os.getenv('WRDS_USERNAME')
        wrds_password = os.getenv('WRDS_PASSWORD')
        return {'wrds_username': wrds_username, 'wrds_password': wrds_password}
    else:
        raise FileNotFoundError("secrets.env file not found")

def test_wrds_connection():
    '''
    Test WRDS connection with credentials from secrets.env.
    '''
    credentials = load_wrds_credentials()
    db = wrds.Connection(
        wrds_username=credentials['wrds_username'],
        wrds_password=credentials['wrds_password']
    )
    print("Connection to WRDS successful!")
    db.close()

if __name__ == '__main__':
    try:
        test_wrds_connection()
    except Exception as e:
        print(f"Error connecting to WRDS: {e}")