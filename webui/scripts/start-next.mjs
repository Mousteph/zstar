import { spawn } from "node:child_process";

import { getFrontendRuntimeConfig } from "../src/server/runtime-config.mjs";

const mode = process.argv[2];
if (!["dev", "start"].includes(mode)) {
  throw new Error("Usage: node scripts/start-next.mjs dev|start");
}

const { host, port } = getFrontendRuntimeConfig();

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
