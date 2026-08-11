"use client";

import { useState } from "react";
import {
  LiveKitRoom,
  RoomAudioRenderer,
  useConnectionState,
  useLocalParticipant,
  useRemoteParticipants,
} from "@livekit/components-react";
import { ConnectionState } from "livekit-client";
import "@livekit/components-styles";

export default function Home() {
  const [token, setToken] = useState("");
  const [serverUrl, setServerUrl] = useState("");
  const [started, setStarted] = useState(false);
  const [loading, setLoading] = useState(false);

  async function startConversation() {
    try {
      setLoading(true);

      const response = await fetch("/api/token", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          room_name: `day4-room-${Date.now()}`,
          participant_identity: `user-${Date.now()}`,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Unable to connect");
      }

      setToken(data.participantToken);
      setServerUrl(data.serverUrl);
      setStarted(true);
    } catch (error) {
      console.error(error);
      alert("Could not connect to the voice agent.");
    } finally {
      setLoading(false);
    }
  }

  function endConversation() {
    setStarted(false);
    setToken("");
    setServerUrl("");
  }

  if (started && token && serverUrl) {
    return (
      <LiveKitRoom
        token={token}
        serverUrl={serverUrl}
        connect={true}
        audio={true}
        video={false}
        onDisconnected={endConversation}
      >
        <ConversationScreen onEnd={endConversation} />
        <RoomAudioRenderer />
      </LiveKitRoom>
    );
  }

  return (
    <main className="landing">
      <div className="card">
        <div className="logo">✦</div>

        <p className="eyebrow">AI VOICE ASSISTANT</p>

        <h1>Can we talk?</h1>

        <p className="subtitle">
          Have a natural conversation with your multilingual AI voice
          assistant.
        </p>

        <button
          className="talk-button"
          onClick={startConversation}
          disabled={loading}
        >
          {loading ? "Connecting..." : "🎙️ Start Talking"}
        </button>

        <div className="features">
          <span>🎧 Voice conversation</span>
          <span>🌐 Multilingual</span>
          <span>🧠 Memory enabled</span>
        </div>
      </div>
    </main>
  );
}

function ConversationScreen({ onEnd }: { onEnd: () => void }) {
  const connectionState = useConnectionState();
  const { isMicrophoneEnabled } = useLocalParticipant();
  const remoteParticipants = useRemoteParticipants();

  const agentConnected = remoteParticipants.length > 0;

  return (
    <main className="conversation">
      <div className="conversation-card">
        <div className="top">
          <div className="logo small">✦</div>

          <div>
            <p className="eyebrow">LIVE CONVERSATION</p>
            <h2>AI Voice Assistant</h2>
          </div>
        </div>

        <div className="orb-container">
          <div className={`orb ${agentConnected ? "active" : ""}`}>
            <span>🎙️</span>
          </div>
        </div>

        <div className="status">
          <span
            className={`status-dot ${
              agentConnected ? "connected" : ""
            }`}
          />

          {connectionState === ConnectionState.Connected
            ? agentConnected
              ? "Your AI assistant is listening"
              : "Connecting to your AI assistant..."
            : "Connecting..."}
        </div>

        <p className="hint">
          {isMicrophoneEnabled
            ? "Speak naturally. I'm listening."
            : "Microphone is disabled."}
        </p>

        <button className="end-button" onClick={onEnd}>
          End Conversation
        </button>
      </div>
    </main>
  );
}