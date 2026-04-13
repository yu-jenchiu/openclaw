import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";

import {
  calendarTodayTool,
  calendarTomorrowTool,
  calendarWeekTool,
  calendarDateTool,
  calendarAddTool,
  calendarDeleteTool,
} from "./tools/calendar-tools.js";

export default definePluginEntry({
  id: "calendar-tools",
  name: "Calendar Tools",
  description: "Google Calendar query/add/delete tools for OpenClaw",
  register(api) {
    api.registerTool(calendarTodayTool);
    api.registerTool(calendarTomorrowTool);
    api.registerTool(calendarWeekTool);
    api.registerTool(calendarDateTool);
    api.registerTool(calendarAddTool);
    api.registerTool(calendarDeleteTool);
  },
});