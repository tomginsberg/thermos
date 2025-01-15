"use client"

import {useState, useEffect} from 'react'
import {CartesianGrid, Line, LineChart, XAxis, YAxis, ResponsiveContainer, Tooltip} from "recharts"
import {format, parseISO} from 'date-fns'

import {
    ChartConfig,
    ChartContainer,
    ChartTooltip,
    ChartTooltipContent,
} from "@/components/ui/chart"
import {processChartData, generateXAxisTicks} from '@/lib/processChartData'
import {Card, CardContent} from "@/components/ui/card.tsx";

const chartConfig = {
    temperature: {
        label: "Temperature",
        color: "hsl(var(--chart-1))",
    },
    setpoint: {
        label: "Setpoint",
        color: "hsl(var(--chart-2))",
    },
} satisfies ChartConfig

function formatHourAmPm(date) {
    let hours = date.getHours(); // Get the hour (0-23)
    const amPm = hours >= 12 ? 'pm' : 'am'; // Determine am or pm
    hours = hours % 12 || 12; // Convert 0 (midnight) and 12 (noon) to 12
    return `${hours}${amPm}`; // Concatenate the formatted hour and am/pm
}


export function TemperatureChart({downsampleRate = 10}) {
    const [chartData, setChartData] = useState([])
    const [xAxisTicks, setXAxisTicks] = useState([])
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        setIsLoading(true);
        setError(null);
        fetch('https://heat-api.xpnz.ca/get_full_history')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Raw data:', data);
                if (!data || !Array.isArray(data.temperature) || !Array.isArray(data.setpoint) || !Array.isArray(data.time)) {
                    throw new Error('Data is not in the expected format');
                }
                const combinedData = data.time.map((time: string, index: string | number) => ({
                    time,
                    temperature: data.temperature[index],
                    setpoint: data.setpoint[index]
                }));
                const processedData = processChartData(combinedData, downsampleRate);
                console.log('Processed data:', processedData);
                setXAxisTicks(generateXAxisTicks(processedData));
                setChartData(processedData);
                setIsLoading(false);
            })
            .catch(error => {
                console.error('Error fetching or processing data:', error);
                setChartData([]);
                setXAxisTicks([]);
                setError(error.message);
                setIsLoading(false);
            });
    }, [])

    if (isLoading) {
        return <div>Loading...</div>;
    }

    if (error) {
        return <div>Error: {error}</div>;
    }

    return (
        <ChartContainer config={chartConfig} className="h-[400px] ">
            <ResponsiveContainer width="100%" height="100%">
                <LineChart
                    data={chartData}
                    margin={{
                        top: 5,
                        right: 30,
                        left: 10,
                        bottom: 5,
                    }}
                >
                    <CartesianGrid strokeDasharray="3 3"/>
                    <XAxis
                        dataKey="time" // the ISO string
                        tickFormatter={(value: string) => {
                            // parse the ISO string and display "HH:mm"
                            const date = parseISO(value);
                            return formatHourAmPm(date);
                        }}
                        ticks={xAxisTicks} // array of ISO strings
                        // tickCount={6}
                        tick={{stroke: 'white'}}
                    />
                    <YAxis
                        domain={['dataMin - 0.5', 'dataMax + 0.5']}
                        tickCount={5}
                        tick={{stroke: 'white'}}
                        tickFormatter={
                            (value: number) => `${value.toFixed(1)}°C`
                        }
                    />
                    <Tooltip
                        contentStyle={{
                            backgroundColor: 'rgba(0,0,0)',
                            borderColor: '#444',
                            color: '#fff'
                        }}
                        labelFormatter={x => `Time: ${format(parseISO(x), 'HH:mm')}`}
                    />
                    {/*<ChartTooltip content={<ChartTooltipContent/>} labelFormatter={x => `Time: ${format(x, 'HH:mm')}`}/>*/}
                    <Line
                        type="monotone"
                        dataKey="temperature"
                        stroke="var(--color-temperature)"
                        strokeWidth={2}
                        dot={false}
                    />
                    <Line
                        type="monotone"
                        dataKey="setpoint"
                        stroke="var(--color-setpoint)"
                        strokeWidth={2}
                        dot={false}
                    />
                </LineChart>
            </ResponsiveContainer>
        </ChartContainer>
    )
}

