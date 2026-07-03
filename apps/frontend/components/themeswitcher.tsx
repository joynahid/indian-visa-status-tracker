"use client";

import { Moon, Sun } from "lucide-react";
import { useState, useEffect } from "react";
import { useTheme } from "next-themes";

export default function ThemeSwitch() {
  const [mounted, setMounted] = useState(false);
  const { systemTheme, theme, setTheme } = useTheme();
  const currentTheme = theme === "system" ? systemTheme : theme;

  useEffect(() => setMounted(true), []);

  if (!mounted) return <>...</>;

  if (currentTheme === "dark") {
    return <Sun className="h-6 w-6 cursor-pointer" onClick={() => setTheme("light")} />;
  }

  if (currentTheme === "light") {
    return (
      <Moon className="h-6 w-6 text-gray-900 cursor-pointer" onClick={() => setTheme("dark")} />
    );
  }
}
