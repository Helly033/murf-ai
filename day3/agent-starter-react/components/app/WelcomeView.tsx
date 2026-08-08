"use client";

import { useState } from "react";

export function WelcomeView({ onStart }: { onStart: () => void }) {
  const [micError, setMicError] = useState<string | null>(null);

  const handleStartWithMicCheck = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach((track) => track.stop());
      setMicError(null);
      onStart();
    } catch (err: any) {
      if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
        setMicError(
          "Microphone access blocked! Please click the lock icon in your browser URL bar to allow microphone permissions."
        );
      } else {
        setMicError("Microphone not detected. Please check your audio settings.");
      }
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-slate-950 text-white p-6">
      {/* BRANDING & TRACK TITLE */}
      <h1 className="text-4xl font-extrabold text-indigo-400 mb-2">
        Aria — Tech Mentor
      </h1>
      <p className="text-gray-400 mb-8 text-center max-w-md">
        Your interactive AI voice mentor for technical interview prep and coding.
      </p>

      {/* STEP 4: MIC ERROR BANNER */}
      {micError && (
        <div className="p-4 mb-6 text-sm text-red-200 bg-red-900/90 border border-red-500 rounded-xl text-center max-w-md shadow-lg animate-bounce">
          ⚠️ {micError}
        </div>
      )}

      {/* READY STATE START BUTTON */}
      <button
        onClick={handleStartWithMicCheck}
        className="px-8 py-4 bg-indigo-600 hover:bg-indigo-500 text-white text-lg font-bold rounded-full shadow-lg transition-all transform hover:scale-105 active:scale-95"
      >
        Start Conversation
      </button>
    </div>
  );
}