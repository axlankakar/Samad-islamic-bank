from app import create_app
import argparse

def main():
    parser = argparse.ArgumentParser(description='Run the Flask application')
    parser.add_argument('--port', type=int, default=5001, help='Port to run the application on')
    args = parser.parse_args()

    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=args.port)

if __name__ == '__main__':
    main() 