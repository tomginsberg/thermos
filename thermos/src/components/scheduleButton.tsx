"use client"

import * as React from "react"
import {useToast} from "@/hooks/use-toast"

import {motion, AnimatePresence} from "framer-motion"
import {
    Drawer,
    DrawerContent,
    DrawerDescription,
    DrawerHeader,
    DrawerTitle,
    DrawerTrigger,
    DrawerFooter, DrawerClose
} from "@/components/ui/drawer"
import {Slider} from "@/components/ui/slider"
import {TimePicker} from "@/components/ui/time-picker"
import {Label} from "@/components/ui/label"
import {Button} from "@/components/ui/button"
import {CalendarClock} from "lucide-react";

// Define the shape of the schedule in your React state
interface ScheduleState {
    weekdayWakeup: string
    weekdayLeave: string
    weekdayReturn: string
    weekdayBed: string
    weekendWakeup: string
    weekendBed: string
    atHomeTemp: number
    atWorkTemp: number
    sleepTemp: number
    isEnabled: boolean
}

export default function ScheduleButton() {
    const {toast} = useToast()
    const [schedule, setSchedule] = React.useState<ScheduleState>({
        weekdayWakeup: "07:30",
        weekdayLeave: "10:00",
        weekdayReturn: "17:00",
        weekdayBed: "22:00",
        weekendWakeup: "08:30",
        weekendBed: "23:00",
        atHomeTemp: 19,
        atWorkTemp: 16,
        sleepTemp: 17,
        isEnabled: true
    })

    // --------------------------
    // 1. Fetch the existing schedule from backend on mount
    // --------------------------
    React.useEffect(() => {
        const fetchSchedule = async () => {
            try {
                const res = await fetch("https://heat-api.xpnz.ca/get_schedule")
                const data = await res.json()

                // data should look like:
                // {
                //   "weekday_wakeup_time": "07:30:00",
                //   "leave_for_work_time": "09:00:00",
                //   "home_from_work_time": "17:00:00",
                //   "weekday_bedtime": "22:00:00",
                //   "weekend_wakeup_time": "08:00:00",
                //   "weekend_bedtime": "23:30:00",
                //   "bedtime_temperature": 17.0,
                //   "wakeup_temperature": 20.0,
                //   "at_work_temperature": 16.0
                // }

                setSchedule(prev => ({
                    ...prev,
                    weekdayWakeup: data.weekday_wakeup_time?.slice(0, 5) || "07:30",
                    weekdayLeave: data.leave_for_work_time?.slice(0, 5) || "09:00",
                    weekdayReturn: data.home_from_work_time?.slice(0, 5) || "17:00",
                    weekdayBed: data.weekday_bedtime?.slice(0, 5) || "22:00",
                    weekendWakeup: data.weekend_wakeup_time?.slice(0, 5) || "08:00",
                    weekendBed: data.weekend_bedtime?.slice(0, 5) || "23:00",
                    sleepTemp: data.bedtime_temperature ?? 17,
                    atHomeTemp: data.wakeup_temperature ?? 20,
                    atWorkTemp: data.at_work_temperature ?? 16,
                    isEnabled: true // or whatever logic you prefer
                }))
            } catch (error) {
                toast(
                    {
                        title: "Error fetching schedule",
                        description: `An error occurred while fetching schedule: ${error}`,
                        variant: "destructive"
                    }
                )
                console.error("Error fetching schedule:", error)
            }
        }

        fetchSchedule()
    }, [])

    // --------------------------
    // 2. Handler logic for updates
    // --------------------------
    const handleTimeChange = (key: keyof ScheduleState, value: string) => {
        setSchedule(prev => ({...prev, [key]: value}))
    }

    const handleTempChange = (key: keyof ScheduleState, value: number[]) => {
        setSchedule(prev => ({...prev, [key]: value[0]}))
    }

    const handleToggle = async (checked: boolean) => {
        // Update local state immediately so UI stays responsive
        setSchedule((prev) => ({...prev, isEnabled: checked}))

        // Make a POST request to /toggle_schedule with the new schedule state
        try {
            const response = await fetch("https://heat-api.xpnz.ca/toggle_schedule", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({state: checked})  // key name can be anything, e.g. `enabled: checked`
            })

            if (!response.ok) {
                throw new Error(`Toggle schedule failed: ${response.statusText}`)
            }
            const data = await response.json()
            console.log("Toggle schedule response:", data)
            toast({
                title: "Schedule updated",
                description: `Schedule is now ${checked ? "enabled" : "disabled"}`,
            })
            // e.g. { status: 'success' }
        } catch (error) {
            toast(
                {
                    title: "Error toggling schedule",
                    description: `An error occurred while toggling schedule: ${error}`,
                    variant: "destructive"
                }
            )
            console.error("Error toggling schedule:", error)
        }
    }

    // --------------------------
    // 3. Save to backend
    // --------------------------
    const handleSave = async () => {
        console.log("Saving schedule:", schedule)
        toast({
            title: "Saving schedule...",
            description: "Please wait while we save your schedule",
        })

        // If your backend does not care about "isEnabled", you can omit it
        if (!schedule.isEnabled) {
            // Decide what you want to do here if schedule is disabled
            // Possibly send a default schedule or skip saving
            return
        }

        // Map your local state to the exact fields the backend expects
        const payload = {
            weekday_wakeup_time: schedule.weekdayWakeup,   // "07:30"
            leave_for_work_time: schedule.weekdayLeave,    // "10:00"
            home_from_work_time: schedule.weekdayReturn,   // "17:00"
            weekday_bedtime: schedule.weekdayBed,          // "22:00"
            weekend_wakeup_time: schedule.weekendWakeup,   // "08:30"
            weekend_bedtime: schedule.weekendBed,          // "23:00"
            bedtime_temperature: schedule.sleepTemp,       // 17
            wakeup_temperature: schedule.atHomeTemp,       // 19
            at_work_temperature: schedule.atWorkTemp       // 16
        }

        try {
            const response = await fetch("https://heat-api.xpnz.ca/set_schedule", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({schedule: payload})
            })

            if (!response.ok) {
                throw new Error(`Failed to save schedule: ${response.statusText}`)
            }

            const result = await response.json()
            console.log("Schedule saved. Server response:", result)
            setOpen(false)
            toast({
                title: "Schedule saved!",
                description: "Your schedule has been saved successfully",
                variant: "success"
                })
        } catch (error) {
            console.error("Error saving schedule:", error)
            toast({
                title: "Error saving schedule",
                description: `An error occurred while saving your schedule ${error}`,
                variant: "destructive"
            })
        }
    }

    const [open, setOpen] = React.useState(false)

    return (
        <Drawer open={open} onOpenChange={setOpen}>
            <DrawerTrigger asChild>
                <Button variant="outline" className="text-xl w-full bg-blue-900 p-4">
                    <CalendarClock/> Schedule
                </Button>
            </DrawerTrigger>
            <DrawerContent className="text-white max-h-screen">
                <DrawerHeader>
                    <DrawerTitle>Thermostat Schedule</DrawerTitle>
                    <DrawerDescription>
                        Set your weekly temperature schedule
                    </DrawerDescription>
                </DrawerHeader>

                <div className="p-4 space-y-6 overflow-y-scroll">
                    {/* Toggle Schedule On/Off */}
                    <div className="flex flex-row items-center justify-center gap-2">
                        <Label htmlFor="schedule-toggle">Schedule Status</Label>
                        <Button
                            id="schedule-toggle"
                            className={`${schedule.isEnabled ? "bg-green-500" : "bg-red-500"}`}
                            onClick={() => handleToggle(!schedule.isEnabled)}
                        >
                            {schedule.isEnabled ? "Enabled" : "Disabled"}
                        </Button>
                    </div>

                    {/* Animate collapsible area only if schedule is enabled */}
                    <AnimatePresence>
                        {schedule.isEnabled && (
                            <motion.div
                                initial={{height: 0, opacity: 0}}
                                animate={{height: "auto", opacity: 1}}
                                exit={{height: 0, opacity: 0}}
                                transition={{duration: 0.3}}
                                className="space-y-6 overflow-hidden pb-6"
                            >
                                {/* Time settings */}
                                <div
                                    className="grid grid-cols-2 sm:grid-cols-3 gap-4 border p-4 rounded-lg border-zinc-500">
                                    <TimePicker
                                        label="Weekday Wake Up"
                                        value={schedule.weekdayWakeup}
                                        onChange={(val) => handleTimeChange("weekdayWakeup", val)}
                                    />
                                    <TimePicker
                                        label="Weekday Leave for Work"
                                        value={schedule.weekdayLeave}
                                        onChange={(val) => handleTimeChange("weekdayLeave", val)}
                                    />
                                    <TimePicker
                                        label="Weekday Return Home"
                                        value={schedule.weekdayReturn}
                                        onChange={(val) => handleTimeChange("weekdayReturn", val)}
                                    />
                                    <TimePicker
                                        label="Weekday Bedtime"
                                        value={schedule.weekdayBed}
                                        onChange={(val) => handleTimeChange("weekdayBed", val)}
                                    />
                                    <TimePicker
                                        label="Weekend Wake Up"
                                        value={schedule.weekendWakeup}
                                        onChange={(val) => handleTimeChange("weekendWakeup", val)}
                                    />
                                    <TimePicker
                                        label="Weekend Bedtime"
                                        value={schedule.weekendBed}
                                        onChange={(val) => handleTimeChange("weekendBed", val)}
                                    />
                                </div>

                                {/* Temperature settings */}
                                <div className="space-y-4 border p-4 rounded-lg border-zinc-500">
                                    <div>
                                        <Label>At Home Temperature: {schedule.atHomeTemp}°C</Label>
                                        <Slider
                                            value={[schedule.atHomeTemp]}
                                            onValueChange={(val) => handleTempChange("atHomeTemp", val)}
                                            min={16}
                                            max={22}
                                            step={0.5}
                                            className="py-4"
                                        />
                                    </div>
                                    <div>
                                        <Label>At Work Temperature: {schedule.atWorkTemp}°C</Label>
                                        <Slider
                                            value={[schedule.atWorkTemp]}
                                            onValueChange={(val) => handleTempChange("atWorkTemp", val)}
                                            min={16}
                                            max={22}
                                            step={0.5}
                                            className="py-4"
                                        />
                                    </div>
                                    <div>
                                        <Label>Sleep Temperature: {schedule.sleepTemp}°C</Label>
                                        <Slider
                                            value={[schedule.sleepTemp]}
                                            onValueChange={(val) => handleTempChange("sleepTemp", val)}
                                            min={16}
                                            max={22}
                                            step={0.5}
                                            className="py-4"
                                        />
                                    </div>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>


                {/* Footer with Cancel/Save */}
                <DrawerFooter className="flex flex-row justify-between">
                    <DrawerClose asChild>
                        <Button
                            variant="outline"
                        >
                            Cancel
                        </Button>
                    </DrawerClose>
                    <Button onClick={handleSave} disabled={!schedule.isEnabled}>
                        Save Schedule
                    </Button>
                </DrawerFooter>
            </DrawerContent>
        </Drawer>
    )
}