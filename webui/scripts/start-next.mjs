import { spawn } from "node:child_process";

import { getAppConfig } from "../src/server/read-config.mjs";

const mode = process.argv[2];
if (!["dev", "start"].includes(mode)) {
  throw new Error("Usage: node scripts/start-next.mjs dev|start");
}

const { host, port } = getAppConfig().frontend;

const child = spawn(
  "npm",
  ["run", mode, "--", "--hostname", host, "--port", String(port)],
  {
    stdio: "inherit",
  },
);

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }

  process.exit(code ?? 1);
});
