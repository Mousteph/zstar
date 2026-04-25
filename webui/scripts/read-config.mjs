import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { parse } from "yaml";

function configPath() {
  for (const candidate of ["config.yaml", "../config.yaml"]) {
    const resolved = resolve(candidate);
    if (existsSync(resolved)) {
      return resolved;
    }
  }

  return resolve("config.yaml");
}

function assertString(value, fieldName) {
  if (typeof value !== "string" || value.trim() === "") {
    throw new Error(`Invalid config field '${fieldName}'. Expected non-empty string.`);
  }

  return value;
}

function assertPort(value, fieldName) {
  if (!Number.isInteger(value) || value < 1 || value > 65535) {
    throw new Error(`Invalid config field '${fieldName}'. Expected integer from 1 to 65535.`);
  }

  return value;
}

function readConfig() {
  const path = configPath();
  const config = parse(readFileSync(path, "utf8"));

  if (!config || typeof config !== "object" || !config.frontend || typeof config.frontend !== "object") {
    throw new Error(`Invalid config file '${path}'. Expected a frontend section.`);
  }

  return {
    frontend: {
      host: assertString(config.frontend.host, "frontend.host"),
      port: assertPort(config.frontend.port, "frontend.port"),
      backend_proxy_url: assertString(config.frontend.backend_proxy_url, "frontend.backend_proxy_url"),
    },
  };
}

export const appConfig = readConfig();
