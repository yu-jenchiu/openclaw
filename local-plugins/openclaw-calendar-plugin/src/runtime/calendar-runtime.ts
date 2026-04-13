import { spawn } from "node:child_process";
import path from "node:path";
import fs from "node:fs";

export class CalendarRuntime {
  private pythonBin(): string {
    return process.env.CALENDAR_PYTHON_BIN || "python";
  }

  private serviceRoot(): string {
    return (
      process.env.CALENDAR_SERVICE_ROOT ||
      path.resolve(process.cwd(), "../calendar_service")
    );
  }

  private scriptPath(): string {
    return (
      process.env.CALENDAR_TOOL_SCRIPT ||
      path.join(this.serviceRoot(), "scripts", "calendar_tool_cli.py")
    );
  }

  private async run(args: string[]): Promise<string> {
    const script = this.scriptPath();

    if (!fs.existsSync(script)) {
      throw new Error(`calendar_tool_cli.py not found: ${script}`);
    }

    return new Promise((resolve, reject) => {
      const proc = spawn(
        this.pythonBin(),
        [script, ...args],
        { cwd: this.serviceRoot() }
      );

      let stdout = "";
      let stderr = "";

      proc.stdout.on("data", (d) => (stdout += d.toString()));
      proc.stderr.on("data", (d) => (stderr += d.toString()));

      proc.on("close", (code) => {
        if (code === 0) {
          resolve(stdout.trim());
        } else {
          reject(
            new Error(
              `calendar CLI failed (exit=${code})\nstdout:\n${stdout}\nstderr:\n${stderr}`
            )
          );
        }
      });
    });
  }

  async today() {
    return this.run(["today"]);
  }

  async tomorrow() {
    return this.run(["tomorrow"]);
  }

  async week() {
    return this.run(["week"]);
  }

  async date(month: number, day: number) {
    return this.run([
      "date",
      "--month",
      String(month),
      "--day",
      String(day),
    ]);
  }

  async add(input: {
    date_type: "today" | "tomorrow" | "date";
    month?: number;
    day?: number;
    time: string;
    summary: string;
  }) {
    const args = ["add", "--time", input.time, "--summary", input.summary];

    if (input.date_type === "today") {
      args.push("--today");
    } else if (input.date_type === "tomorrow") {
      args.push("--tomorrow");
    } else {
      args.push(
        "--month",
        String(input.month),
        "--day",
        String(input.day)
      );
    }

    return this.run(args);
  }

  async delete(keyword: string) {
    return this.run(["delete", "--keyword", keyword]);
  }
}