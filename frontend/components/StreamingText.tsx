"use client";

import { useEffect, useRef, useState } from "react";


function StreamingText({
    text,
    speed = 30,
    onComplete,
  }: {
    text: string;
    speed?: number;
    onComplete?: () => void;
}) {
    const [displayed, setDisplayed] = useState("");

    useEffect(() => {
        let index = 0;
        const interval = setInterval(() => {
            if (index < text.length){
                setDisplayed(text.slice(0, index + 1));
                index++;
            } else{ 
                clearInterval(interval);
                onComplete?.();
            }
        }, speed);
        return () => clearInterval(interval);
    }, [text, speed, onComplete]);

    return <span>{displayed}</span>;
}

export default StreamingText;