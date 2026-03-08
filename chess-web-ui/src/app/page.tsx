"use client";

import { useRouter } from "next/navigation";
import { useAuth } from "../context/AuthContext";
import React, { useEffect } from "react";

export default function Page() {
    const router = useRouter();
    const { isAuthenticated, isLoading } = useAuth();

    useEffect(() => {
        if (!isLoading) {
            if (isAuthenticated) {
                router.push("/play");
            } else {
                router.push("/login");
            }
        }
    }, [isLoading, isAuthenticated, router]);

    return (
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "100vh" }}>
            <p>Loading...</p>
        </div>
    );
}
