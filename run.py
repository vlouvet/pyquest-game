from pq_app.app import app  # Ensure you are importing the Flask app instance

if __name__ == "__main__":
    # Ensure 'app' is a Flask app or similar with a 'run' method
    try:
        app.run(debug=True)
    except AttributeError:
        print("Error: 'app' does not have a 'run' method. Make sure 'app' is a Flask (or similar) application instance.")