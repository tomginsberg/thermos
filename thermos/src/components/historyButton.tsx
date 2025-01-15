import {History} from "lucide-react";
import {Button} from "@/components/ui/button.tsx";
import {
    Drawer,
    DrawerTitle,
    DrawerContent,
    DrawerTrigger,
    DrawerDescription
} from "@/components/ui/drawer.tsx";
import {TemperatureChart} from "@/components/temperatureChart.tsx";
import {useState} from "react";

export default function HistoryButton() {
    const [key, setKey] = useState(0);

    const handleDrawerOpen = () => {
        setKey(prevKey => prevKey + 1);
    };

    return (
        <Drawer>
            <DrawerTrigger asChild>
                <Button variant="outline" className=" text-xl w-[150px] p-4" onClick={handleDrawerOpen}> <
                    History/> History
                </Button>
            </DrawerTrigger>
            <DrawerContent>
                <DrawerTitle className="text-white py-8 text-center text-4xl">Temperature History</DrawerTitle>
                <DrawerDescription className="hidden">Here is the history of your thermostat</DrawerDescription>
                <TemperatureChart key={key}/>
            </DrawerContent>
        </Drawer>
    )
}