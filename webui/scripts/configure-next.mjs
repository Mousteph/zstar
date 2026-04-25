import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

function defaultConfigPath() {
  for (const candidate of ["config.yaml", "../config.yaml"]) {
    const resolved = resolve(candidate);
    if (existsSync(resolved)) {
      return resolved;
    }
  }

  return resolve("config.yaml");
}

const configPath = defaultConfigPath();
const configText = readFileSync(configPath, "utf8");

function sectionValue(sectionName, fieldName) {
  const lines = configText.split(/\r?\n/);
  let inSection = false;

  for (const line of lines) {
    if (line.trim().startsWith("#") || line.trim() === "") {
      continue;
    }

    if (!line.startsWith(" ") && !line.startsWith("\t")) {
      inSection = line.trim() === `${sectionName}:`;
      continue;
    }

    if (!inSection) {
      continue;
    }

    const match = line.match(new RegExp(String.raw`^\s{2}${fieldName}:\s*["']?([^"'\n#]+)["']?\s*(?:#.*)?$`));
    if (match) {
      return match[1].trim();
    }
  }

  throw new Error(`Missing '${sectionName}.${fieldName}' in ${configPath}.`);
}

const backendProxyUrl = sectionValue("frontend", "backend_proxy_url");
const frontendHost = sectionValue("frontend", "host");
const frontendPort = sectionValue("frontend", "port");

export { backendProxyUrl, frontendHost, frontendPort };
