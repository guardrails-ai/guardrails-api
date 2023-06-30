from app import create_app
import os 

if __name__ == '__main__':
    stage = os.environ.get('STAGE', 'local')
    the_port = 8000
    app = create_app()
    app.run(host='0.0.0.0', port=the_port)