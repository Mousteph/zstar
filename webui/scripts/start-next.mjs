import { spawn } from "node:child_process";

import { backendProxyUrl, frontendHost, frontendPort } from "./configure-next.mjs";

const mode = process.argv[2];
if (!["dev", "start"].includes(mode)) {
  throw new Error("Usage: node scripts/start-next.mjs dev|start");
}

const child = spawn(
  "npm",
  ["run", mode, "--", "--hostname", frontendHost, "--port", frontendPort],
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
