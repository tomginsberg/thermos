window.addEventListener("load", function() {
    const apiUrl = 'http://localhost:1111';
    let temperatureData = [];
    let setpointData = [];
    let categories = [];

    function updateChartData() {
        axios.get(`${apiUrl}/get_history`)
            .then(response => {
                const data = response.data;
                temperatureData = data.temperature;
                setpointData = data.setpoint;
                categories = temperatureData.map((_, index) => `Point ${index + 1}`);
                updateChart();
            })
            .catch(error => {
                if (error.response) {
                    // The request was made and the server responded with a status code
                    // that falls out of the range of 2xx
                    console.error("Error response data:", error.response.data);
                    console.error("Error response status:", error.response.status);
                    console.error("Error response headers:", error.response.headers);
                } else if (error.request) {
                    // The request was made but no response was received
                    console.error("Error request:", error.request);
                } else {
                    // Something happened in setting up the request that triggered an Error
                    console.error('Error', error.message);
                }
                console.error("Error config:", error.config);
            });
    }


    function updateHeaterState() {
        axios.get(`${apiUrl}/get_heater_state`)
            .then(response => {
                const heaterState = response.data.heater_state ? "Heat is On" : "Heat is Off";
                document.getElementById("heater-state").textContent = heaterState;
            })
            .catch(error => console.error("Error fetching heater state:", error));
    }

    let chartOptions = {
        series: [
            {
                name: "Temperature",
                data: temperatureData,
                color: "#1A56DB",
            },
            {
                name: "Setpoint",
                data: setpointData,
                color: "#7E3BF2",
            },
        ],
        chart: {
            type: "line",
            height: "100%",
            maxWidth: "100%",
            fontFamily: "Inter, sans-serif",
        },
        xaxis: {
            categories: categories,
        },
        // ... other ApexCharts options ...
    };

    let temperatureChart = new ApexCharts(document.getElementById("temperature-chart"), chartOptions);
    temperatureChart.render();

    function updateChart() {
        temperatureChart.updateOptions({
            xaxis: { categories: categories },
            series: [
                { data: temperatureData },
                { data: setpointData },
            ],
        });
    }

    updateChartData();
    updateHeaterState();
    setInterval(updateChartData, 5000); // Update chart every 5 seconds
    setInterval(updateHeaterState, 5000); // Update heater state every 5 seconds
});
