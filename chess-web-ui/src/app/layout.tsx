import type { Metadata } from "next";
import { AuthProvider } from "../context/AuthContext";
import "./globals.css";

export const metadata: Metadata = {
    title: "Chess Engine",
    description: "Play chess against AI or other players",
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en">
            <body>
                <AuthProvider>
                    {children}
                </AuthProvider>
            </body>
        </html>
    );
}

