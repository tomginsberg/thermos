"use client"

import * as React from "react"
import * as SliderPrimitive from "@radix-ui/react-slider"

import { cn } from "@/lib/utils"

const Slider = React.forwardRef<
    React.ElementRef<typeof SliderPrimitive.Root>,
    React.ComponentPropsWithoutRef<typeof SliderPrimitive.Root>
>(({ className, orientation = "horizontal", ...props }, ref) => (
    <SliderPrimitive.Root
        ref={ref}
        className={cn(
            "relative flex touch-none select-none items-center",
            orientation === "horizontal" ? "w-full h-4" : "h-full w-4 flex-col",
            className
        )}
        orientation={orientation}
        {...props}
    >
      <SliderPrimitive.Track
          className={cn(
              "relative grow rounded-full",
              orientation === "horizontal" ? "h-4 bg-gradient-to-r" : "w-10 bg-gradient-to-t",
              "from-blue-500 to-red-500"
          )}
      >
        <SliderPrimitive.Range className="absolute bg-white bg-opacity-30 rounded-full" />
      </SliderPrimitive.Track>
      <SliderPrimitive.Thumb
          className={cn("block rounded-full border-2 border-primary bg-zinc-100  ring-offset-zinc-100 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-4 disabled:pointer-events-none disabled:opacity-50",
              orientation === "horizontal" ? "w-8 h-8" : "h-16 w-16")}
      />
    </SliderPrimitive.Root>
))
Slider.displayName = SliderPrimitive.Root.displayName

export { Slider }

