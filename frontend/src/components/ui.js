import React from "react";
import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";

export function Button({ variant = "primary", className = "", children, ...props }) {
  const base =
    "inline-flex items-center justify-center gap-2 font-medium rounded-sm px-5 py-2.5 text-sm transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed select-none";
  const variants = {
    primary: "bg-primary text-white hover:bg-primary-hover",
    outline: "border border-line text-ink bg-white hover:border-ink hover:bg-surface",
    ghost: "text-ink hover:bg-surface",
    danger: "bg-danger text-white hover:opacity-90",
    dark: "bg-ink text-white hover:bg-primary",
  };
  return (
    <button className={`${base} ${variants[variant]} ${className}`} {...props}>
      {children}
    </button>
  );
}

export function Card({ className = "", hover = false, children, ...props }) {
  return (
    <div
      className={`bg-white border border-line rounded-sm ${
        hover ? "transition-all duration-200 hover:-translate-y-0.5 hover:border-ink" : ""
      } ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}

export function Input({ label, className = "", testid, ...props }) {
  return (
    <label className="block">
      {label && <span className="block text-sm font-medium text-ink mb-1.5">{label}</span>}
      <input
        data-testid={testid}
        className={`w-full rounded-sm border border-line bg-white px-3.5 py-2.5 text-sm text-ink outline-none transition-colors focus:border-primary placeholder:text-muted ${className}`}
        {...props}
      />
    </label>
  );
}

export function Textarea({ label, className = "", testid, ...props }) {
  return (
    <label className="block">
      {label && <span className="block text-sm font-medium text-ink mb-1.5">{label}</span>}
      <textarea
        data-testid={testid}
        className={`w-full rounded-sm border border-line bg-white px-3.5 py-2.5 text-sm text-ink outline-none transition-colors focus:border-primary placeholder:text-muted ${className}`}
        {...props}
      />
    </label>
  );
}

export function Select({ label, className = "", testid, children, ...props }) {
  return (
    <label className="block">
      {label && <span className="block text-sm font-medium text-ink mb-1.5">{label}</span>}
      <select
        data-testid={testid}
        className={`w-full rounded-sm border border-line bg-white px-3 py-2.5 text-sm text-ink outline-none transition-colors focus:border-primary ${className}`}
        {...props}
      >
        {children}
      </select>
    </label>
  );
}

export function Spinner({ className = "" }) {
  return <Loader2 className={`animate-spin ${className}`} />;
}

export function FullSpinner() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-white">
      <Spinner className="w-7 h-7 text-primary" />
    </div>
  );
}

const scoreColor = (s) =>
  s >= 75 ? "#198754" : s >= 50 ? "#002FA7" : "#DC3545";

export function ScoreBar({ label, score, testid }) {
  return (
    <div data-testid={testid}>
      <div className="flex justify-between items-baseline mb-1">
        <span className="text-sm font-medium text-ink">{label}</span>
        <span className="text-sm font-semibold" style={{ color: scoreColor(score) }}>
          {score}
        </span>
      </div>
      <div className="h-2 w-full bg-surface rounded-sm overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${score}%` }}
          transition={{ duration: 0.7, ease: "easeOut" }}
          className="h-full rounded-sm"
          style={{ backgroundColor: scoreColor(score) }}
        />
      </div>
    </div>
  );
}

export function Pill({ children, className = "" }) {
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 text-xs font-medium rounded-sm border ${className}`}>
      {children}
    </span>
  );
}

export const fadeUp = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4, ease: "easeOut" },
};
