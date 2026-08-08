"use client";

import { LiveKitRoom, RoomAudioRenderer, StartAudio, useConnectionState } from "@livekit/components-react";
import { ConnectionState } from "livekit-client";
import { useState } from "react";

function RoomView({ onDisconnect }: { onDisconnect: () => void }) {
  const roomState = useConnectionState();

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-slate-950 text-white p-6">
      <h1 className="text-4xl font-extrabold text-indigo-400 mb-2">Aria — Tech Mentor</h1>

      {roomState === ConnectionState.Connecting && (
        <div className="flex flex-col items-center my-6">
          <div className="w-12 h-12 border-4 border-yellow-400 border-t-transparent rounded-full animate-spin mb-4"></div>
          <p className="text-yellow-400 text-lg">Connecting to Aria voice agent...</p>
        </div>
      )}

      {roomState === ConnectionState.Connected && (
        <div className="flex flex-col items-center my-6">
          <div className="w-3 h-3 bg-green-500 rounded-full animate-ping mb-2"></div>
          <p className="text-green-400 text-lg font-semibold mb-4">Connected! Speak into your microphone...</p>
          <StartAudio label="Click here to enable audio" className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 font-bold rounded-full text-white shadow-lg cursor-pointer" />
        </div>
      )}

      <button
        onClick={onDisconnect}
        className="mt-6 px-6 py-2 bg-red-600 hover:bg-red-500 text-white font-semibold rounded-full shadow-md transition-all cursor-pointer"
      >
        End Call
      </button>

      <RoomAudioRenderer />
    </div>
  );
}

export default function Page() {
  const [inCall, setInCall] = useState(false);

  // LiveKit WebSocket URL
  const livekitUrl = "wss://pr1-d7r19rtr.livekit.cloud";
  
  // Your generated token
  const token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiU3R1ZGVudCIsInZpZGVvIjp7InJvb21Kb2luIjp0cnVlLCJyb29tIjoiYXJpYS1yb29tIiwiY2FuUHVibGlzaCI6dHJ1ZSwiY2FuU3Vic2NyaWJlIjp0cnVlLCJjYW5QdWJsaXNoRGF0YSI6dHJ1ZX0sInN1YiI6IlN0dWRlbnQiLCJpc3MiOiJBUElSWnB4enRLdHM1UzkiLCJuYmYiOjE3ODYxODg3NDAsImV4cCI6MTc4NjIxMDM0MH0.hAPZVMHHs7lHlFCZ2m78n9eg3eekBnyl4ioR3AlY_h0"

  if (!inCall) {
    return (
      <main className="flex flex-col items-center justify-center min-h-screen bg-slate-950 text-white p-6">
        <h1 className="text-4xl font-extrabold text-indigo-400 mb-2">Aria — Tech Mentor</h1>
        <p className="text-gray-400 mb-8 text-center max-w-md">
          Your interactive AI voice mentor for technical interview prep and coding.
        </p>
        <button
          onClick={() => setInCall(true)}
          className="px-8 py-4 bg-indigo-600 hover:bg-indigo-500 text-white text-lg font-bold rounded-full shadow-lg transition-all transform hover:scale-105 cursor-pointer"
        >
          Start Conversation
        </button>
      </main>
    );
  }

  return (
    <LiveKitRoom
      audio={true}
      video={false}
      token={token}
      serverUrl={livekitUrl}
      data-lk-theme="default"
      onDisconnected={() => setInCall(false)}
    >
      <RoomView onDisconnect={() => setInCall(false)} />
    </LiveKitRoom>
  );
}