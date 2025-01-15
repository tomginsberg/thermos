"use client"

import {useState, useEffect} from 'react'
import {CartesianGrid, Line, LineChart, XAxis, YAxis, Tooltip} from "recharts"
import {format, parseISO} from 'date-fns'

import {
    ChartConfig,
    ChartContainer,
} from "@/components/ui/chart"
import {processChartData, generateXAxisTicks, generateYAxisTicks} from '@/lib/processChartData'
import {Skeleton} from "@/components/ui/skeleton";

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

function formatHourAmPm(date: Date) {
    let hours = date.getHours(); // Get the hour (0-23)
    const amPm = hours >= 12 ? 'pm' : 'am'; // Determine am or pm
    hours = hours % 12 || 12; // Convert 0 (midnight) and 12 (noon) to 12
    return `${hours}:${date.getMinutes()}${amPm}`; // Concatenate the formatted hour and am/pm
}


export function TemperatureChart({downsampleRate = 10}) {
    const [chartData, setChartData] = useState([])
    const [xAxisTicks, setXAxisTicks] = useState([])
    const [yAxisTicks, setYAxisTicks] = useState([])
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
                if (!data || !Array.isArray(data.temperature) || !Array.isArray(data.setpoint) || !Array.isArray(data.time)) {
                    throw new Error('Data is not in the expected format');
                }
                const combinedData = data.time.map((time: string, index: string | number) => ({
                    time,
                    temperature: data.temperature[index],
                    setpoint: data.setpoint[index]
                }));
                const processedData = processChartData(combinedData, downsampleRate);
                // @ts-expect-error - processedData is an array of objects
                setXAxisTicks(generateXAxisTicks(processedData))
                // @ts-expect-error - processedData is an array of objects
                setYAxisTicks(generateYAxisTicks(processedData))
                // @ts-expect-error - processedData is an array of objects
                setChartData(processedData)
                setIsLoading(false)
            })
            .catch(error => {
                console.error('Error fetching or processing data:', error);
                setChartData([]);
                setXAxisTicks([]);
                setError(error.message);
                setIsLoading(false);
            });
    }, [downsampleRate])

    if (isLoading) {
        return <Skeleton className="h-[384px] bg-zinc-200 opacity-20 mx-8 mb-4"/>;
    }

    if (error) {
        return <div>Error: {error}</div>;
    }

    return (
        <ChartContainer config={chartConfig} className="h-[400px] ">
                <LineChart
                    data={chartData}
                    margin={{
                        top: 5,
                        right: 30,
                        left: 10,
                        bottom: 20,
                    }}
                >
                    <CartesianGrid strokeDasharray="3 3"/>
                    <XAxis
                        dataKey="time" // the ISO string
                        tickFormatter={(value: string) => {
                            // if (value===xAxisTicks[xAxisTicks.length - 1]) {
                            //     return 'now'}
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
                        ticks={yAxisTicks}
                        tick={{stroke: 'white'}}
                        tickFormatter={
                            (value: number) => `${value}°C`
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
        </ChartContainer>
    )
}

