import {toZonedTime} from 'date-fns-tz';

interface RawDataPoint {
    temperature: number;
    setpoint: number;
    time: string; // e.g. "Tue, 14 Jan 2025 23:23:41 GMT"
}

interface ProcessedDataPoint {
    time: string;  // formatted to "HH:mm" for display
    temperature: number;
    setpoint: number;
}

// Make sure you have proper imports:
// import { format } from 'date-fns';
// import { utcToZonedTime } from 'date-fns-tz';

export function processChartData(
    data: RawDataPoint[],
    downsampleRate: number = 10
): ProcessedDataPoint[] {
    return data
        .filter((_, index) => index % downsampleRate === 0)
        .map((point) => {
            // Convert the raw UTC date string to Date, then to EST
            const utcDate = new Date(point.time); // e.g. "Tue, 14 Jan 2025 23:23:41 GMT"
            // find the clients timezone
            const clientTimeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
            const estDate = toZonedTime(utcDate, clientTimeZone);
            estDate.setHours(estDate.getHours() + 5); // EST is 4 hours behind UTC

            // Return an ISO string plus any other data
            return {
                // The key part: store an ISO string so Recharts can parse it
                time: estDate.toISOString(),
                temperature: point.temperature,
                setpoint: point.setpoint,
            };
        });
}


export function generateXAxisTicks(data: ProcessedDataPoint[]): string[] {
    if (data.length === 0) return [];
    const step = Math.floor(data.length / 6);
    return data
        .filter((_, index) => index % step === 0)
        .map(point => point.time);
}

export function generateYAxisTicks(data: ProcessedDataPoint[]): number[] {
    if (data.length === 0) return []
    const minTemp = Math.min(...data.map(point => Math.min(point.temperature, point.setpoint)))
    const maxTemp = Math.max(...data.map(point => Math.max(point.temperature, point.setpoint)))
    return Array.from({length: maxTemp - minTemp + 1}, (_, index) => minTemp + index)
}