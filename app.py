from flask import Flask, request, jsonify
import numpy as np
import pickle
from scipy.stats import boxcox

app = Flask(__name__)

# Load the model
MODEL_FILE = "earthquake.pkl"
try:
    with open(MODEL_FILE, "rb") as model_file:
        model = pickle.load(model_file)
    print("✅ Model loaded successfully!")
except FileNotFoundError:
    print(f"❌ Model file '{MODEL_FILE}' not found. Please ensure it's in the same directory.")

# Hardcoded lambda values for Box-Cox transformation
lambdas = {
    "speed_lambda": 0.5704643439440645,
    "dist_lambda": 0.5508930423799914,
    "other1_lambda": 0.5704643439440645,
    "other2_lambda": -0.2665410973455398,
}

@app.route("/")
def home():
    return "🚀 Earthquake Prediction API is running!"

@app.route("/predict", methods=["POST"])
def predict():
    """API endpoint for earthquake prediction."""
    try:
        # Get JSON data
        data = request.json

        # Validate 'features' key
        if "features" not in data:
            return jsonify({"error": "No features provided"}), 400

        # Extract features
        features = np.array(data["features"])

        # Debug print to check received data
        print("📡 Received features:", features)

        # Validate length of features
        if len(features) != 4:
            return jsonify({"error": f"Incorrect number of features. Expected 4, got {len(features)}"}), 400

        # Apply Box-Cox transformation to each feature
        try:
            boxcox_speed = boxcox(features[0] + 1, lambdas["speed_lambda"])
            boxcox_dist = boxcox(features[1] + 1, lambdas["dist_lambda"])
            boxcox_other1 = boxcox(features[2] + 1, lambdas["other1_lambda"])
            boxcox_other2 = boxcox(features[3] + 1, lambdas["other2_lambda"])
        except Exception as e:
            return jsonify({"error": f"Box-Cox transformation failed: {str(e)}"}), 500

        # Create transformed feature array
        features_transformed = np.array([boxcox_speed, boxcox_dist, boxcox_other1, boxcox_other2]).reshape(1, -1)

        # Make prediction
        prediction = model.predict(features_transformed)

        # Return the prediction
        return jsonify({"prediction": int(prediction[0])})

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
