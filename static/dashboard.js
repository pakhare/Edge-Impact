
let intervalId;
let previousTrafficVolume = 1000;
let previousUserCount = 500;
let previousLatency = 30;

// Select elements
const startButton = document.querySelector('.strt');
const stopButton = document.querySelector('.stop');
const locationSelect = document.getElementById('location');
const trafficDisplay = document.getElementById('traffic');
const usersDisplay = document.getElementById('users');
const latencyDisplay = document.getElementById('latency');
const traditionalPercent = document.getElementById('traditionalpercent');
const solarPercent = document.getElementById('solarpercent');
const windPercent = document.getElementById('windpercent');
const hydroPercent = document.getElementById('hydropercent');

// Disable buttons initially
startButton.disabled = false;
stopButton.disabled = true;

// // Enable the Start button when a location is selected
// locationSelect.addEventListener('change', () => {
//     startButton.disabled = false;
// });

// Start Simulation logic
async function startSimulation() {
    const gh = locationSelect.value;
    if (!gh) {
        // If no location is selected, show tooltip
        document.getElementById('tltp').innerHTML = "Please select a location.";
        return; // Do not start the simulation
    }
    document.getElementById('tltp').innerHTML = "";
    document.getElementById('spn').style.display = 'none';
    const selectedLocation = locationSelect.value;

    // Disable Start button and enable Stop button
    startButton.disabled = true;
    stopButton.disabled = false;

    try {
        // Call the API to get power distribution for the selected location
        const locationResponse = await fetch(`/simulationLocation?location=${encodeURIComponent(selectedLocation)}`);
        if (!locationResponse.ok) {
            throw new Error('Location API call failed');
        }
        
        document.getElementById('ggt').innerHTML = "Getting weather data for " + selectedLocation + " ...";
        setTimeout(() => {
            document.getElementById('ggt').innerHTML = "Predicting with watsonx ai IBM-Granite Model ..."
        }, 300);
                // Assuming locationResponse is the response from Flask
        const locationData = await locationResponse.json();
        console.log(locationData)
        // Now locationData directly contains the power source values
        traditionalPercent.innerText = `${locationData.traditional}%`;
        solarPercent.innerText = `${locationData.solar}%`;
        windPercent.innerText = `${locationData.wind}%`;
        hydroPercent.innerText = `${locationData.hydropower}%`;

        setTimeout(() => {
            document.getElementById('ggt').innerHTML = "Prediction Succeeded."
        }, 600);

        document.getElementById('powerrusage').style.display = 'block';
        // Start the simulation
        intervalId = setInterval(async () => {
            // Randomize values for network simulation
            let trafficVolume = previousTrafficVolume + Math.floor(Math.random() * 21) - 10;
            let userCount = previousUserCount + Math.floor(Math.random() * 21) - 10;
            let latency = previousLatency + Math.floor(Math.random() * 11) - 5;

            // Keep the values within ranges
            trafficVolume = Math.max(800, Math.min(trafficVolume, 2000));
            userCount = Math.max(100, Math.min(userCount, 1000));
            latency = Math.max(10, Math.min(latency, 100));

            // Call the simulation API
            const response = await fetch('/simulate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'bypass-tunnel-reminder': 'any_value'
                },
                body: JSON.stringify({
                    traffic_volume: trafficVolume,
                    user_count: userCount,
                    latency: latency,
                    packet_loss: 0.1,
                    signal_strength: 75,
                    weather_condition: 'Clear',
                    hour: 12,
                    day: 5,
                    month: 10
                })
            });

            if (!response.ok) {
                throw new Error('Simulation API call failed');
            }

            const data = await response.json();
            const predictedEnergy = parseFloat(data.predicted_energy);

            if (!isNaN(predictedEnergy)) {
                // Update the power bar and network stats
                const normalizedPowerLevel = Math.min(Math.max(predictedEnergy, 0), 100);
                document.getElementById('powerpercent').innerText = `${normalizedPowerLevel.toFixed(2)}%`;

                trafficDisplay.innerText = trafficVolume;
                usersDisplay.innerText = userCount;
                latencyDisplay.innerText = latency;

                // Save the current values
                previousTrafficVolume = trafficVolume;
                previousUserCount = userCount;
                previousLatency = latency;
            }
        }, 2000);
    } catch (error) {
        console.error('Error during simulation:', error);
    }
}

// Stop Simulation logic
function stopSimulation() {
    clearInterval(intervalId);
    document.getElementById('spn').style.display = 'block';
    document.getElementById('powerrusage').style.display = 'none';
    document.getElementById('ggt').innerHTML = "";
    // Disable Stop button and enable Start button
    stopButton.disabled = true;
    startButton.disabled = false;
}