# Mountain Safety Predictor Web App

## Setup

### Backend

1.  Navigate to the backend directory:

    ```bash
    cd backend
    ```

2.  Install Node.js dependencies:

    ```bash
    npm install
    ```

3.  Install Python dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4.  **Important:** Since the actual trained model is not available, you need to generate a dummy model for testing purposes. Run:

    ```bash
    python train_dummy_model.py
    ```

    _If you have the real `model.joblib` file, place it in the `backend` directory instead._

5.  Start the server:
    ```bash
    npm start
    ```
    The server will run on `http://localhost:3000`.

### Frontend

1.  Open `frontend/index.html` in your web browser.
2.  You can use a simple HTTP server if you prefer, e.g., with Python:
    ```bash
    cd frontend
    python -m http.server 8000
    ```
    Then visit `http://localhost:8000`.

## Usage

1.  Select an **Activity Type**.
2.  Select an **Experience Level**.
3.  Pick a **Date**.
4.  Click on the **Map** to select a location.
5.  Click **Check Safety**.

The application will fetch weather data for the selected location and date (including previous 2 days), run the classification model, and display whether the conditions are predicted to be Safe or Dangerous.
