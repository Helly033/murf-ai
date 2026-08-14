import { NextResponse } from "next/server";
import Database from "better-sqlite3";
import path from "path";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const dbPath = path.join(
      process.cwd(),
      "..",
      "call_analytics.db"
    );

    const db = new Database(dbPath, {
      readonly: true,
    });

    const calls = db.prepare(`
      SELECT
        id,
        call_id,
        room_name,
        start_time,
        end_time,
        duration,
        status,
        outcome,
        human_handoff,
        transcript
      FROM calls
      ORDER BY id DESC
    `).all();

    const totalCalls = calls.length;

    const completedCalls = calls.filter(
      (call: any) => call.status === "completed"
    ).length;

    const humanHandoffs = calls.filter(
      (call: any) => Number(call.human_handoff) === 1
    ).length;

    const durations = calls
      .filter(
        (call: any) =>
          call.status === "completed" &&
          Number(call.duration) > 0
      )
      .map((call: any) => Number(call.duration));

    const averageDuration =
      durations.length > 0
        ? Math.round(
            durations.reduce(
              (sum, duration) => sum + duration,
              0
            ) / durations.length
          )
        : 0;

    const outcomeCounts: Record<string, number> = {};

    calls.forEach((call: any) => {
      const outcome = call.outcome || "unknown";

      outcomeCounts[outcome] =
        (outcomeCounts[outcome] || 0) + 1;
    });

    db.close();

    return NextResponse.json({
      summary: {
        totalCalls,
        completedCalls,
        humanHandoffs,
        averageDuration,
      },
      outcomes: outcomeCounts,
      calls,
    });
  } catch (error) {
    console.error("Analytics API error:", error);

    return NextResponse.json(
      {
        error: "Failed to load call analytics",
      },
      { status: 500 }
    );
  }
}