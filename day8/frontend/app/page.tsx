"use client";

import { useEffect, useState } from "react";
import {
  LiveKitRoom,
  RoomAudioRenderer,
  useConnectionState,
  useLocalParticipant,
  useRemoteParticipants,
} from "@livekit/components-react";
import { ConnectionState } from "livekit-client";
import "@livekit/components-styles";

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from "chart.js";

import { Bar, Doughnut } from "react-chartjs-2";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);


// =========================================================
// TYPES
// =========================================================

type CallRecord = {
  id: number;
  call_id: string;
  room_name: string;
  start_time: string;
  end_time: string | null;
  duration: number;
  status: string;
  outcome: string | null;
  human_handoff: number;
  transcript: string | null;
};

type AnalyticsData = {
  summary: {
    totalCalls: number;
    completedCalls: number;
    humanHandoffs: number;
    averageDuration: number;
  };
  outcomes: Record<string, number>;
  calls: CallRecord[];
};


// =========================================================
// MAIN PAGE
// =========================================================

export default function Home() {
  const [token, setToken] = useState("");
  const [serverUrl, setServerUrl] = useState("");
  const [started, setStarted] = useState(false);
  const [loading, setLoading] = useState(false);

  const [analytics, setAnalytics] =
    useState<AnalyticsData | null>(null);

  const [analyticsLoading, setAnalyticsLoading] =
    useState(true);

  const [analyticsError, setAnalyticsError] =
    useState("");


  // -------------------------------------------------------
  // Load analytics
  // -------------------------------------------------------
async function loadAnalytics() {
  try {
    const response = await fetch("/api/analytics", {
      method: "GET",
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(`Analytics API returned ${response.status}`);
    }

    const data = await response.json();
    setAnalytics(data);
    setAnalyticsError("");
  } catch (error) {
    console.error("Analytics error:", error);

    // Keep existing dashboard data if a single polling request fails.
    setAnalyticsError("");
  }
}


  // -------------------------------------------------------
  // Load analytics on page load
  // -------------------------------------------------------

  useEffect(() => {
    loadAnalytics();

  const interval = setInterval(() => {
  loadAnalytics();
}, 10000);

    return () => clearInterval(interval);
  }, []);


  // -------------------------------------------------------
  // Start conversation
  // -------------------------------------------------------

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
        throw new Error(
          data.error || "Unable to connect"
        );
      }

      setToken(data.participantToken);
      setServerUrl(data.serverUrl);
      setStarted(true);

    } catch (error) {
      console.error(error);

      alert(
        "Could not connect to the voice agent."
      );

    } finally {
      setLoading(false);
    }
  }


  // -------------------------------------------------------
  // End conversation
  // -------------------------------------------------------

  function endConversation() {
    setStarted(false);
    setToken("");
    setServerUrl("");

    // Give backend a moment to save call analytics
    setTimeout(() => {
      loadAnalytics();
    }, 1500);
  }


  // -------------------------------------------------------
  // Voice conversation screen
  // -------------------------------------------------------

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
        <ConversationScreen
          onEnd={endConversation}
        />

        <RoomAudioRenderer />
      </LiveKitRoom>
    );
  }


  // -------------------------------------------------------
  // Dashboard
  // -------------------------------------------------------

  return (
    <main className="dashboard-page">

      {/* ===================================================
          VOICE AGENT HEADER
      =================================================== */}

      <section className="hero-section">

        <div className="hero-card">

          <div className="logo">
            ✦
          </div>

          <p className="eyebrow">
            AI VOICE ASSISTANT
          </p>

          <h1>
            Call Analytics Dashboard
          </h1>

          <p className="subtitle">
            Talk naturally with your multilingual AI
            voice assistant and monitor call performance.
          </p>

          <button
            className="talk-button"
            onClick={startConversation}
            disabled={loading}
          >
            {loading
              ? "Connecting..."
              : "🎙️ Start Talking"}
          </button>

          <div className="features">

            <span>
              🎧 Voice conversation
            </span>

            <span>
              🌐 Multilingual
            </span>

            <span>
              ⚡ Murf Falcon TTS
            </span>

          </div>

        </div>

      </section>


      {/* ===================================================
          ANALYTICS HEADER
      =================================================== */}

      <section className="analytics-section">

        <div className="analytics-header">

          <div>

            <p className="eyebrow">
              DAY 8
            </p>

            <h2>
              📊 Call Analytics
            </h2>

            <p>
              Monitor your AI voice agent performance.
            </p>

          </div>

          <button
            className="refresh-button"
            onClick={loadAnalytics}
            disabled={analyticsLoading}
          >
            {analyticsLoading
              ? "Refreshing..."
              : "↻ Refresh"}
          </button>

        </div>


        {/* =================================================
            ERROR
        ================================================= */}

        {analyticsError && (
          <div className="error-card">
            {analyticsError}
          </div>
        )}


        {/* =================================================
            LOADING
        ================================================= */}

        {analyticsLoading && !analytics && (
          <div className="loading-card">
            Loading call analytics...
          </div>
        )}


        {analytics && (
          <>

            {/* =============================================
                SUMMARY CARDS
            ============================================= */}

            <div className="stats-grid">

              <StatCard
                icon="📞"
                title="Total Calls"
                value={analytics.summary.totalCalls}
              />

              <StatCard
                icon="✅"
                title="Completed Calls"
                value={analytics.summary.completedCalls}
              />

              <StatCard
                icon="🤝"
                title="Human Handoffs"
                value={analytics.summary.humanHandoffs}
              />

              <StatCard
                icon="⏱️"
                title="Avg Duration"
                value={`${analytics.summary.averageDuration}s`}
              />

            </div>


            {/* =============================================
                CHARTS
            ============================================= */}

            <div className="charts-grid">

              {/* -------------------------------------------
                  Call activity
              ------------------------------------------- */}

              <div className="chart-card">

                <h3>
                  📈 Call Activity
                </h3>

                <p className="chart-subtitle">
                  Recent call durations
                </p>

                <div className="chart-container">

                  <Bar
                    data={{
                      labels: analytics.calls
                        .slice()
                        .reverse()
                        .map(
                          (_, index) =>
                            `Call ${index + 1}`
                        ),

                      datasets: [
                        {
                          label: "Duration (seconds)",

                          data: analytics.calls
                            .slice()
                            .reverse()
                            .map(
                              (call) =>
                                Number(
                                  call.duration
                                )
                            ),

                          borderWidth: 1,
                        },
                      ],
                    }}

                    options={{
                      responsive: true,

                      maintainAspectRatio: false,

                      plugins: {
                        legend: {
                          display: false,
                        },
                      },

                      scales: {
                        y: {
                          beginAtZero: true,
                        },
                      },
                    }}
                  />

                </div>

              </div>


              {/* -------------------------------------------
                  Outcomes
              ------------------------------------------- */}

              <div className="chart-card">

                <h3>
                  📊 Call Outcomes
                </h3>

                <p className="chart-subtitle">
                  Distribution of call outcomes
                </p>

                <div className="doughnut-container">

                  {Object.keys(
                    analytics.outcomes
                  ).length > 0 ? (

                    <Doughnut
                      data={{
                        labels: Object.keys(
                          analytics.outcomes
                        ),

                        datasets: [
                          {
                            label: "Calls",

                            data: Object.values(
                              analytics.outcomes
                            ),

                            borderWidth: 2,
                          },
                        ],
                      }}

                      options={{
                        responsive: true,

                        maintainAspectRatio: false,

                        plugins: {
                          legend: {
                            position: "bottom",
                          },
                        },
                      }}
                    />

                  ) : (
                    <p>
                      No outcome data yet.
                    </p>
                  )}

                </div>

              </div>

            </div>


            {/* =============================================
                RECENT CALLS
            ============================================= */}

            <div className="calls-card">

              <div className="calls-header">

                <div>

                  <h3>
                    📋 Recent Calls
                  </h3>

                  <p>
                    Latest voice agent conversations
                  </p>

                </div>

                <span className="call-count">
                  {analytics.calls.length} calls
                </span>

              </div>


              {analytics.calls.length === 0 ? (

                <div className="empty-state">
                  No calls recorded yet.
                </div>

              ) : (

                <div className="table-wrapper">

                  <table>

                    <thead>

                      <tr>
                        <th>Call</th>
                        <th>Time</th>
                        <th>Duration</th>
                        <th>Status</th>
                        <th>Outcome</th>
                        <th>Handoff</th>
                      </tr>

                    </thead>

                    <tbody>

                      {analytics.calls
                        .slice(0, 10)
                        .map((call) => (

                          <tr key={call.id}>

                            <td>
                              <code>
                                {call.call_id.slice(
                                  0,
                                  8
                                )}
                                ...
                              </code>
                            </td>

                            <td>
                              {new Date(
                                call.start_time
                              ).toLocaleTimeString()}
                            </td>

                            <td>
                              {call.duration || 0}s
                            </td>

                            <td>

                              <span
                                className={`status-badge ${
                                  call.status ===
                                  "completed"
                                    ? "completed"
                                    : "active"
                                }`}
                              >
                                {call.status}
                              </span>

                            </td>

                            <td>
                              {call.outcome ||
                                "unknown"}
                            </td>

                            <td>
                              {Number(
                                call.human_handoff
                              ) === 1
                                ? "🤝 Yes"
                                : "No"}
                            </td>

                          </tr>

                        ))}

                    </tbody>

                  </table>

                </div>

              )}

            </div>

          </>
        )}

      </section>


      {/* ===================================================
          FOOTER
      =================================================== */}

      <footer>

        <p>
          AI Voice Agent powered by{" "}
          <strong>Murf Falcon</strong>
        </p>

      </footer>

    </main>
  );
}


// =========================================================
// STAT CARD
// =========================================================

function StatCard({
  icon,
  title,
  value,
}: {
  icon: string;
  title: string;
  value: string | number;
}) {

  return (
    <div className="stat-card">

      <div className="stat-icon">
        {icon}
      </div>

      <div>

        <p className="stat-title">
          {title}
        </p>

        <h3>
          {value}
        </h3>

      </div>

    </div>
  );
}


// =========================================================
// CONVERSATION SCREEN
// =========================================================

function ConversationScreen({
  onEnd,
}: {
  onEnd: () => void;
}) {

  const connectionState =
    useConnectionState();

  const { localParticipant } =
    useLocalParticipant();

  const remoteParticipants =
    useRemoteParticipants();

  const agentConnected =
    remoteParticipants.length > 0;

  const isMicrophoneEnabled =
    localParticipant.isMicrophoneEnabled;


  return (
    <main className="landing">

      <div className="card">

        <div className="logo">
          ✦
        </div>

        <p className="eyebrow">
          AI VOICE ASSISTANT
        </p>

        <h1>
          {connectionState ===
          ConnectionState.Connected
            ? "We're connected"
            : "Connecting..."}
        </h1>

        <div className="status">

          <span
            className={`status-dot ${
              agentConnected
                ? "connected"
                : ""
            }`}
          />

          {connectionState ===
          ConnectionState.Connected
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

        <button
          className="end-button"
          onClick={onEnd}
        >
          End Conversation
        </button>

      </div>

    </main>
  );
}