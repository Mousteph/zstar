import type { Metadata } from "next";
import type { ReactNode } from "react";

import "@/app/globals.css";

export const metadata: Metadata = {
  title: "ZStar",
};

const THEME_BOOTSTRAP_SCRIPT = `(function(){try{var persistedTheme=localStorage.getItem("zstar.theme");var themeClass=persistedTheme==="light"?"light":"dark";document.documentElement.classList.remove("dark","light");document.documentElement.classList.add(themeClass);}catch(error){document.documentElement.classList.remove("dark","light");document.documentElement.classList.add("dark");console.warn("Failed to read persisted theme from localStorage.",error);}})();`;

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <script dangerouslySetInnerHTML={{ __html: THEME_BOOTSTRAP_SCRIPT }} />
        {children}
      </body>
    </html>
  );
}
