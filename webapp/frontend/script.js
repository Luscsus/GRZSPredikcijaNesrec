const map = L.map("map").setView([46.1512, 14.9955], 8); // Center on Slovenia

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "&copy; OpenStreetMap contributors",
}).addTo(map);

let selectedLat = null;
let selectedLon = null;
let marker = null;

map.on("click", function (e) {
  selectedLat = e.latlng.lat;
  selectedLon = e.latlng.lng;

  if (marker) {
    map.removeLayer(marker);
  }
  marker = L.marker([selectedLat, selectedLon]).addTo(map);

  document.getElementById(
    "location-display"
  ).innerText = `${selectedLat.toFixed(4)}, ${selectedLon.toFixed(4)}`;
});

document.getElementById("check-btn").addEventListener("click", async () => {
  const activity = document.getElementById("activity").value;
  const experience = document.getElementById("experience").value;
  const date = document.getElementById("date").value;

  if (!selectedLat || !selectedLon) {
    alert("Prosim izberite lokacijo na zemljevidu.");
    return;
  }
  if (!date) {
    alert("Prosim izberite datum.");
    return;
  }

  const resultDiv = document.getElementById("result");
  const predictionText = document.getElementById("prediction-text");
  const weatherInfo = document.getElementById("weather-info");

  resultDiv.classList.add("hidden");
  predictionText.innerText = "Nalaganje...";
  resultDiv.className = "";

  try {
    // 1. Get Weather Data
    const weatherResponse = await axios.get("http://localhost:3000/weather", {
      params: {
        lat: selectedLat,
        lon: selectedLon,
        date: date,
      },
    });

    const weatherData = weatherResponse.data;

    weatherInfo.innerHTML = `
            <p>Temperatura: ${weatherData.Temp_tisti_dan}°C</p>
            <p>Dež: ${weatherData.Kolicina_dezja_tisti_dan}mm</p>
            <p>Sneg: ${weatherData.Snezenje_cm_tisti_dan}cm</p>
        `;

    // 2. Get Prediction
    const predictResponse = await axios.post("http://localhost:3000/predict", {
      activity: activity,
      experience: experience,
      lat: selectedLat,
      lon: selectedLon,
      weather: weatherData,
    });

    const prediction = predictResponse.data;

    resultDiv.classList.remove("hidden");
    if (prediction.safe) {
      predictionText.innerText = `VARNO (${(
        prediction.probability * 100
      ).toFixed(1)}%)`;
      resultDiv.classList.add("safe");
    } else {
      predictionText.innerText = `NEVARNO (${(
        prediction.probability * 100
      ).toFixed(1)}%)`;
      resultDiv.classList.add("dangerous");
    }
  } catch (error) {
    console.error(error);
    alert("Prišlo je do napake. Preverite konzolo za podrobnosti.");
  }
});
