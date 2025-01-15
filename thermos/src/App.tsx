import Thermostat from '@/components/thermostat'
import {TemperatureChart} from "@/components/temperatureChart.tsx";

export default function Home() {
    return (
        <main className="min-h-screen flex justify-center w-screen p-8 bg-black md:bg-zinc-300 text-white">
            <div className="md:border md:rounded-xl md:border-zinc-100 md:block md:px-8 bg-black md:drop-shadow-2xl">
               <Thermostat/>
            </div>
        </main>
    )
}

