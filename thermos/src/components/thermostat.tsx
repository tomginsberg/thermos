'use client'

import {useState, useEffect, useRef} from 'react'
import {Slider} from "@/components/ui/slider"
import {Button} from "@/components/ui/button"
import {History, CalendarClock} from 'lucide-react'

const SLIDER_MIN = 16
const SLIDER_MAX = 22
const UPDATE_INTERVAL = 500
const API = 'http://cobalt:1111'

const marks = Array.from({length: SLIDER_MAX - SLIDER_MIN + 1}, (_, index) => ({
    value: SLIDER_MAX - index,
    label: `${SLIDER_MAX - index}°C`,
}))

const getTemperatureColor = (temperature: number) => {
    const minTemp = 16;
    const maxTemp = 22;

    // Ensure the temperature is clamped within the range
    const clampedTemp = Math.max(minTemp, Math.min(maxTemp, temperature));

    // Calculate interpolation factor (0 to 1)
    const factor = (clampedTemp - minTemp) / (maxTemp - minTemp);

    // Tailwind's blue-500 (rgb(59, 130, 246)) and red-500 (rgb(239, 68, 68))
    const blueRGB = [59, 130, 246];
    const redRGB = [239, 68, 68];

    // Interpolate RGB values
    const interpolatedRGB = blueRGB.map((start, i) =>
        Math.round(start + factor * (redRGB[i] - start))
    );

    // Convert to `rgb()` string
    return `rgb(${interpolatedRGB.join(", ")})`;
};

export default function Thermostat() {
    const [temperature, setTemperature] = useState(20)
    const [heaterState, setHeaterState] = useState(false)
    const [setpoint, setSetpoint] = useState(20)
    const isDraggingRef = useRef(false)

    useEffect(() => {
        const fetchInitialSetpoint = async () => {
            try {
                const response = await fetch(`${API}/get_setpoint`)
                const data = await response.json()
                setSetpoint(data.setpoint)
            } catch (error) {
                console.error('Error fetching initial setpoint:', error)
            }
        }

        fetchInitialSetpoint()
    }, [])

    useEffect(() => {
        const updateTemperatureAndHeaterState = async () => {
            try {
                const [tempResponse, heaterResponse] = await Promise.all([
                    fetch(`${API}/get_temperature`),
                    fetch(`${API}/get_heater_state`)
                ])
                const tempData = await tempResponse.json()
                const heaterData = await heaterResponse.json()
                setTemperature(tempData.temperature)
                setHeaterState(heaterData.heater_state)
            } catch (error) {
                console.error('Error updating temperature and heater state:', error)
            }
        }

        const intervalId = setInterval(updateTemperatureAndHeaterState, UPDATE_INTERVAL)
        return () => clearInterval(intervalId)
    }, [])

    useEffect(() => {
        const updateSetpoint = async () => {
            if (isDraggingRef.current) return

            try {
                const response = await fetch(`${API}/get_setpoint`)
                const data = await response.json()
                if (data.setpoint !== setpoint) {
                    setSetpoint(data.setpoint)
                }
            } catch (error) {
                console.error('Error fetching setpoint:', error)
            }
        }

        const intervalId = setInterval(updateSetpoint, UPDATE_INTERVAL)
        return () => clearInterval(intervalId)
    }, [setpoint])

    const handleSetpointChange = async (newValue: number[]) => {
        const newSetpoint = newValue[0]
        setSetpoint(newSetpoint)

        try {
            await fetch(`${API}/set_setpoint`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({setpoint: newSetpoint})
            })
        } catch (error) {
            console.error('Error updating setpoint:', error)
        }
    }

    return (
        <div className="flex items-center justify-center gap-12 h-[calc(100vh-56px)]">
            <div
                className="bg-zinc-900 shadow-md pb-6 shadow-white p-5  rounded-lg flex flex-col justify-between items-end space-y-16 font-mono text-right">
                <div>
                    <h2 className="text-2xl font-bold mb-2">Temperature</h2>
                    <p className="text-5xl" style={{color: getTemperatureColor(temperature)}}>
                        {temperature.toFixed(1)}°C
                    </p>
                </div>
                <div>
                    <h2 className="text-2xl font-bold mb-2">Setpoint</h2>
                    <p className="text-5xl" style={{color: getTemperatureColor(setpoint)}}>{setpoint.toFixed(1)}°C</p>
                </div>
                <div>
                    <h2 className="text-2xl font-bold mb-2">Heater is</h2>
                    <p className={`text-4xl ${heaterState ? "text-red-500" : "text-blue-500"}`}>
                        {heaterState ? "ON" : "OFF"}
                    </p>
                </div>
                <Button variant="outline" className=" text-xl w-[150px] p-4"><History/> History</Button>
                <Button variant="outline" className=" text-xl w-[150px] p-4"><CalendarClock/> Schedule</Button>
            </div>
            <div className="h-[70vh] flex items-center">
                <div className="relative h-full w-24">
                    <div
                        className={`z-50 px-6 absolute w-8 h-8 rounded-xl ${heaterState ? "bg-red-500" : "bg-blue-500"} flex items-center justify-center text-white text-xs font-bold pointer-events-none`}
                        style={{
                            left: 'calc(100% - 2rem)',
                            bottom: `calc(${((temperature - SLIDER_MIN) / (SLIDER_MAX - SLIDER_MIN)) * 100}% - 1rem)`,
                        }}
                    >
                        {temperature.toFixed(1)}°C
                    </div>
                    <Slider
                        orientation="vertical"
                        min={SLIDER_MIN}
                        max={SLIDER_MAX}
                        step={0.001}
                        value={[setpoint]}
                        onValueChange={handleSetpointChange}
                        className="h-full data-[orientation=vertical]:w-8 data-[orientation=vertical]:h-full"
                    />
                    <div className="absolute left-10 top-0 bottom-0 flex flex-col justify-between pointer-events-none">
                        {marks.map((mark) => (
                            <div key={mark.value} className="ps-8 flex items-center">
                                <span className="text-sm text-white">{mark.label}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    )
}
