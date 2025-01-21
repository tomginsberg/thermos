"use client"

import {Label} from "@/components/ui/label"
import {Input} from "@/components/ui/input"

interface TimePickerProps {
    label: string
    value: string
    onChange: (value: string) => void
}

export function TimePicker({label, value, onChange}: TimePickerProps) {
    return (
        <div className="flex flex-col space-y-2">
            <Label className="text-sm">{label}</Label>
            <Input
                type="time"
                value={value}
                onChange={(e) => onChange(e.target.value)}
            />
        </div>
    )
}

