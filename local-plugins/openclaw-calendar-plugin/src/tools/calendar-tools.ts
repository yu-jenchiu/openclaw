import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { Type } from "@sinclair/typebox";

const execFileAsync = promisify(execFile);

const CALENDAR_CLI_CWD =
  process.env.CALENDAR_CLI_CWD || "C:\\Users\\chest\\Desktop\\calendar_service";

const PYTHON_CMD =
  process.env.PYTHON_CMD || (process.platform === "win32" ? "py" : "python3");

type ToolResultDetails = {
  success: boolean;
  args?: string[];
  raw?: string;
  error?: string;
  stdout?: string;
  stderr?: string;
  reason?: string;
};

function makeTextResult(text: string, details: ToolResultDetails) {
  return {
    details,
    content: [
      {
        type: "text" as const,
        text,
      },
    ],
  };
}

async function runCalendarCli(args: string[]) {
  try {
    const { stdout, stderr } = await execFileAsync(
      PYTHON_CMD,
      ["-m", "scripts.calendar_tool_cli", ...args],
      {
        cwd: CALENDAR_CLI_CWD,
        windowsHide: true,
      }
    );

    const text = [stdout, stderr].filter(Boolean).join("\n").trim();

    return makeTextResult(
      text || "Command completed, but no output was returned.",
      {
        success: true,
        args,
        raw: text,
      }
    );
  } catch (error: any) {
    const stdout = error?.stdout ? String(error.stdout) : "";
    const stderr = error?.stderr ? String(error.stderr) : "";
    const message = error?.message ? String(error.message) : "Unknown error";

    const text = [
      "Calendar command failed.",
      message,
      stdout ? `stdout:\n${stdout}` : "",
      stderr ? `stderr:\n${stderr}` : "",
    ]
      .filter(Boolean)
      .join("\n\n");

    return makeTextResult(text, {
      success: false,
      args,
      error: message,
      stdout,
      stderr,
    });
  }
}

export const calendarTodayTool = {
  name: "calendar_today",
  label: "Calendar Today",
  description: "Get today's calendar events.",
  parameters: Type.Object({}),
  async execute(_id: string, _params: Record<string, never>) {
    return runCalendarCli(["today"]);
  },
};

export const calendarTomorrowTool = {
  name: "calendar_tomorrow",
  label: "Calendar Tomorrow",
  description: "Get tomorrow's calendar events.",
  parameters: Type.Object({}),
  async execute(_id: string, _params: Record<string, never>) {
    return runCalendarCli(["tomorrow"]);
  },
};

export const calendarWeekTool = {
  name: "calendar_week",
  label: "Calendar Week",
  description: "Get calendar events for the coming week.",
  parameters: Type.Object({}),
  async execute(_id: string, _params: Record<string, never>) {
    return runCalendarCli(["week"]);
  },
};

export const calendarDateTool = {
  name: "calendar_date",
  label: "Calendar Date",
  description: "Get calendar events for a specific month and day.",
  parameters: Type.Object({
    month: Type.Number({ minimum: 1, maximum: 12 }),
    day: Type.Number({ minimum: 1, maximum: 31 }),
  }),
  async execute(
    _id: string,
    params: {
      month: number;
      day: number;
    }
  ) {
    return runCalendarCli([
      "date",
      "--month",
      String(params.month),
      "--day",
      String(params.day),
    ]);
  },
};

export const calendarAddTool = {
  name: "calendar_add",
  label: "Calendar Add",
  description:
    "Add a calendar event for today, tomorrow, or a specified month/day.",
  parameters: Type.Object({
    date_type: Type.Union([
      Type.Literal("today"),
      Type.Literal("tomorrow"),
      Type.Literal("date"),
    ]),
    month: Type.Optional(Type.Number({ minimum: 1, maximum: 12 })),
    day: Type.Optional(Type.Number({ minimum: 1, maximum: 31 })),
    time: Type.String({
      description: "24-hour time format, e.g. 19:00",
    }),
    summary: Type.String({
      description: "Event title / summary",
    }),
  }),
  async execute(
    _id: string,
    params: {
      date_type: "today" | "tomorrow" | "date";
      month?: number;
      day?: number;
      time: string;
      summary: string;
    }
  ) {
    const args = ["add", "--time", params.time, "--summary", params.summary];

    if (params.date_type === "today") {
      args.push("--today");
    } else if (params.date_type === "tomorrow") {
      args.push("--tomorrow");
    } else {
      if (params.month == null || params.day == null) {
        return makeTextResult(
          "When date_type is 'date', both month and day are required.",
          {
            success: false,
            reason: "missing_month_or_day",
          }
        );
      }

      args.push("--month", String(params.month), "--day", String(params.day));
    }

    return runCalendarCli(args);
  },
};

export const calendarDeleteTool = {
  name: "calendar_delete",
  label: "Calendar Delete",
  description: "Delete calendar events by keyword.",
  parameters: Type.Object({
    keyword: Type.String({
      description: "Keyword used to find the target event(s)",
    }),
  }),
  async execute(
    _id: string,
    params: {
      keyword: string;
    }
  ) {
    return runCalendarCli(["delete", "--keyword", params.keyword]);
  },
};