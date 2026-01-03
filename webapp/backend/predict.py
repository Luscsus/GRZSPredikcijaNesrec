import sys
import json
import pandas as pd
import joblib
import numpy as np

# Define features order exactly as in training
FEATURES = [
 'Izkušenost_drugo',
 'Izkušenost_gorski vodnik',
 'Izkušenost_mladinski vodnik',
 'Izkušenost_planinec nečlan PD',
 'Izkušenost_planinec-član PD',
 'Izkušenost_planinski vodnik',
 'Izkušenost_reševalec',
 'Izkušenost_turist',
 'Dejavnost_alpsko smučanje',
 'Dejavnost_druge športne in rekreacijske aktivnosti',
 'Dejavnost_gorsko kolesarjenje',
 'Dejavnost_planinstvo - brezpotje',
 'Dejavnost_planinstvo - hoja po poti',
 'Dejavnost_plezanje',
 'Dejavnost_turno smučanje',
 'latitude',
 'longitude',
 'Temp_tisti_dan',
 'Kolicina_dezja_tisti_dan',
 'Snezenje_cm_tisti_dan',
 'Temp_prejsni_dan',
 'Temp_preprejsni_dan',
 'Kolicina_dezja_prejsni_dan',
 'Kolicina_dezja_preprejsni_dan',
 'Snezenje_cm_prejsni_dan',
 'Snezenje_cm_preprejsni_dan'
]

def log(msg):
    print(f"[Predict] {msg}", file=sys.stderr)

def main():
    try:
        log("Starting prediction...")
        # Read input from command line argument
        if len(sys.argv) < 2:
            print(json.dumps({"error": "No input data provided"}))
            sys.exit(1)

        input_json = sys.argv[1]
        log(f"Received input: {input_json[:100]}...")
        data = json.loads(input_json)

        # Load model
        try:
            model = joblib.load('model.joblib')
            log(f"Model loaded successfully. Type: {type(model)}")
            if not hasattr(model, 'predict'):
                raise ValueError(f"Loaded model is not a valid classifier (it is {type(model)}). Please regenerate model.joblib.")
        except FileNotFoundError:
            print(json.dumps({"error": "Model file not found. Please run train_dummy_model.py first."}))
            sys.exit(1)

        # Prepare input vector
        input_dict = {feature: 0 for feature in FEATURES}

        # Set numerical values
        input_dict['latitude'] = float(data.get('lat', 0))
        input_dict['longitude'] = float(data.get('lon', 0))

        # Set weather values
        weather = data.get('weather', {})
        for key in weather:
            if key in input_dict:
                input_dict[key] = float(weather[key])

        # Set One-Hot Encoded values
        experience = data.get('experience')
        activity = data.get('activity')

        # Map experience string to column
        exp_key = f"Izkušenost_{experience}"
        if exp_key in input_dict:
            input_dict[exp_key] = 1
        
        # Map activity string to column
        act_key = f"Dejavnost_{activity}"
        if act_key in input_dict:
            input_dict[act_key] = 1

        # Create DataFrame
        df = pd.DataFrame([input_dict])
        log(f"Input DataFrame for prediction: {df.head()}")
        
        # Predict
        prediction = model.predict(df)[0]
        
        probability = 0.0
        if hasattr(model, "predict_proba"):
             probs = model.predict_proba(df)[0]
             probability = probs[int(prediction)]

        result = {
            "prediction": int(prediction),
            "safe": bool(prediction == 0), 
            "probability": float(probability)
        }

        log(f"Prediction result: {result}")
        print(json.dumps(result))

    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stderr)
        log(f"Error: {e}")
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()
