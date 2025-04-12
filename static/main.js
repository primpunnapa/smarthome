async function fetchLatest(place, targetId) {
  const url = `http://localhost:8000/${place}/indoor/lastest`;   // Check if this is correct and matches your FastAPI endpoint
  const outdoorUrl = `http://localhost:8000/${place}/outdoor/lastest`;  // Same here

  try {
    const [indoorRes, outdoorRes] = await Promise.all([
      fetch(url),
      fetch(outdoorUrl),
    ]);

    if (!indoorRes.ok || !outdoorRes.ok) {
      throw new Error('Failed to fetch data');
    }

    const indoor = await indoorRes.json();
    const outdoor = await outdoorRes.json();

    const html = `
      <strong>Indoor</strong><br>
      Temp: ${indoor.temperature}°C<br>
      Humidity: ${indoor.humidity}%<br>
      Time: ${new Date(indoor.recorded_at).toLocaleString()}<br><br>
      <strong>Outdoor</strong><br>
      Temp: ${outdoor.temperature}°C<br>
      Humidity: ${outdoor.humidity}%<br>
      Weather: ${outdoor.weather_main}<br>
      Time: ${new Date(outdoor.recorded_at).toLocaleString()}
    `;

    document.getElementById(targetId).innerHTML = html;
  } catch (err) {
    console.error("Error:", err);
    document.getElementById(targetId).innerText = "Error loading data: " + err.message;
  }
}


document.addEventListener("DOMContentLoaded", () => {
  fetchLatest("KU", "ku-latest");  // ดึงข้อมูลของ KU
  fetchLatest("Ladprao", "ladprao-latest");  // ดึงข้อมูลของ Ladprao
});
