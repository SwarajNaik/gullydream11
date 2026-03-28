import { cn } from "@/lib/utils";
import { forwardRef } from "react";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: string;
  label?: string;
}

const Input = forwardRef<HTMLInputElement, InputProps>(({ className, error, label, ...props }, ref) => (
  <div className="space-y-1">
    {label && <label className="text-sm text-[#9E9E9E]">{label}</label>}
    <input
      ref={ref}
      className={cn(
        "w-full rounded-[8px] bg-[#16213E] border border-[#2A2A4A] px-3 py-2.5 text-white placeholder:text-[#666666] focus:border-[#E94560] focus:outline-none",
        error && "border-red-500",
        className
      )}
      {...props}
    />
    {error && <p className="text-xs text-red-500">{error}</p>}
  </div>
));
Input.displayName = "Input";

export { Input };
