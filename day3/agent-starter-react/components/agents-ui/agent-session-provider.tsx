import { useVoiceAssistant, useConnectionState, BarVisualizer } from "@livekit/components-react";
import { ConnectionState } from "livekit-client";

export function CustomSessionView({ onDisconnect }: { onDisconnect: () => void }) {
  const connectionState = useConnectionState();
  const { state, audioTrack } = useVoiceAssistant();

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-slate-950 text-white p-6">
      <div className="w-full max-w-md p-8 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl flex flex-col items-center gap-6">
        
        {/* AGENT BADGE */}
        <div className="px-4 py-1.5 rounded-full bg-indigo-950 border border-indigo-700 text-indigo-300 text-sm font-semibold">
          Aria | Tech Mentor
        </div>

        {/* STATE DISPLAY MESSAGES */}
        <div className="text-xl font-medium text-center">
          {/* STATE 2: CONNECTING */}
          {connectionState === ConnectionState.Connecting && (
            <p className="text-yellow-400 animate-pulse">Joining call... Please wait.</p>
          )}

          {/* STATE 3: LISTENING */}
          {connectionState === ConnectionState.Connected && state === "listening" && (
            <p className="text-emerald-400 font-bold">🎙️ Listening to you...</p>
          )}

          {/* STATE 4: SPEAKING */}
          {connectionState === ConnectionState.Connected && state === "speaking" && (
            <p className="text-indigo-400 font-bold">🔊 Aria is speaking...</p>
          )}

          {/* THINKING TRANSITION */}
          {connectionState === ConnectionState.Connected && state === "thinking" && (
            <p className="text-purple-400">🧠 Thinking...</p>
          )}

          {/* STATE 5: CALL ENDED / DISCONNECTED */}
          {connectionState === ConnectionState.Disconnected && (
            <p className="text-red-400 font-semibold">Call Ended</p>
          )}
        </div>

        {/* SPEAKER INDICATOR (WAVEFORM VISUALIZER) */}
        {connectionState === ConnectionState.Connected && audioTrack && (
          <div className="w-full h-20 bg-slate-950/60 rounded-xl p-2 border border-slate-800 flex items-center justify-center">
            <BarVisualizer state={state} trackRef={audioTrack} barCount={9} />
          </div>
        )}

        {/* END CALL / START AGAIN BUTTON */}
        <button
          onClick={onDisconnect}
          className="mt-4 px-6 py-2.5 bg-rose-600 hover:bg-rose-500 text-white font-medium rounded-lg transition-colors w-full"
        >
          {connectionState === ConnectionState.Disconnected ? "Start Again" : "End Call"}
        </button>
      </div>
    </div>
  );
}