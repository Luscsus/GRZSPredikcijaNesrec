const express = require("express");
const cors = require("cors");
const bodyParser = require("body-parser");
const axios = require("axios");
const { spawn } = require("child_process");
const path = require("path");

const app = express();
const PORT = 3000;

app.use(cors());
app.use(bodyParser.json());

function formatDate(date) {
  return date.toISOString().split("T")[0];
}

app.get("/weather", async (req, res) => {
  try {
    const { lat, lon, date } = req.query;

    if (!lat || !lon || !date) {
      return res.status(400).json({ error: "Missing lat, lon, or date" });
    }

    const targetDate = new Date(date);
    const startDate = new Date(targetDate);
    startDate.setDate(startDate.getDate() - 2); // 2 days before

    const startDateStr = formatDate(startDate);
    const endDateStr = formatDate(targetDate);

    // Fetch weather data
    const weatherUrl = "https://api.open-meteo.com/v1/forecast";
    const response = await axios.get(weatherUrl, {
      params: {
        latitude: lat,
        longitude: lon,
        daily: "temperature_2m_mean,rain_sum,snowfall_sum",
        start_date: startDateStr,
        end_date: endDateStr,
        timezone: "auto",
      },
    });

    const daily = response.data.daily;

    if (!daily || !daily.time || daily.time.length < 3) {
      return res
        .status(500)
        .json({ error: "Could not fetch complete weather history" });
    }

    const weatherData = {
      Temp_tisti_dan: daily.temperature_2m_mean[2],
      Temp_prejsni_dan: daily.temperature_2m_mean[1],
      Temp_preprejsni_dan: daily.temperature_2m_mean[0],
      Kolicina_dezja_tisti_dan: daily.rain_sum[2],
      Kolicina_dezja_prejsni_dan: daily.rain_sum[1],
      Kolicina_dezja_preprejsni_dan: daily.rain_sum[0],
      Snezenje_cm_tisti_dan: daily.snowfall_sum[2],
      Snezenje_cm_prejsni_dan: daily.snowfall_sum[1],
      Snezenje_cm_preprejsni_dan: daily.snowfall_sum[0],
    };

    res.json(weatherData);
  } catch (error) {
    console.error("Error fetching weather:", error.message);
    res.status(500).json({ error: "Failed to fetch weather data" });
  }
});

app.post("/predict", (req, res) => {
  const inputData = req.body;

  // Spawn python process
  const pythonProcess = spawn("python", [
    path.join(__dirname, "predict.py"),
    JSON.stringify(inputData),
  ]);

  let dataString = "";
  let errorString = "";

  pythonProcess.stdout.on("data", (data) => {
    dataString += data.toString();
  });

  pythonProcess.stderr.on("data", (data) => {
    const msg = data.toString();
    console.error(`[Python Log]: ${msg}`);
    errorString += msg;
  });

  pythonProcess.on("close", (code) => {
    if (code !== 0) {
      console.error(`Python process exited with code ${code}`);
      console.error(errorString);
      return res
        .status(500)
        .json({ error: "Prediction failed", details: errorString });
    }

    try {
      const result = JSON.parse(dataString);
      res.json(result);
    } catch (e) {
      console.error("Failed to parse python output:", dataString);
      res.status(500).json({ error: "Invalid output from model" });
    }
  });
});

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
