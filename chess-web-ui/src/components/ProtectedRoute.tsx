"use client";

import React from "react";
import { useAuth } from "../context/AuthContext";
import { useRouter } from "next/navigation";

interface ProtectedRouteProps {
    children: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
    const { isAuthenticated, isLoading } = useAuth();
    const router = useRouter();

    React.useEffect(() => {
        if (!isLoading && !isAuthenticated) {
            router.push("/login");
        }
    }, [isAuthenticated, isLoading, router]);

    if (isLoading) {
        return (
            <div style={{
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                minHeight: "100vh",
                fontSize: "18px",
                color: "#666"
            }}>
                Loading...
            </div>
        );
    }

    if (!isAuthenticated) {
        return null;
    }

    return <>{children}</>;
};

