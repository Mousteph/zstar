import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { parse } from "yaml";

type FrontendConfig = {
  host: string;
  port: number;
  backend_proxy_url: string;
};

type WebConfig = {
  frontend: FrontendConfig;
};

function configPath(): string {
  for (const candidate of ["config.yaml", "../config.yaml"]) {
    const resolved = resolve(candidate);
    if (existsSync(resolved)) {
      return resolved;
    }
  }

  return resolve("config.yaml");
}

function assertString(value: unknown, fieldName: string): string {
  if (typeof value !== "string" || value.trim() === "") {
    throw new Error(`Invalid config field '${fieldName}'. Expected non-empty string.`);
  }

  return value;
}

function assertPort(value: unknown, fieldName: string): number {
  if (typeof value !== "number" || !Number.isInteger(value) || value < 1 || value > 65535) {
    throw new Error(`Invalid config field '${fieldName}'. Expected integer from 1 to 65535.`);
  }

  return value;
}

function readConfig(): WebConfig {
  const path = configPath();
  const rawConfig = parse(readFileSync(path, "utf8")) as unknown;

  if (!rawConfig || typeof rawConfig !== "object" || !("frontend" in rawConfig)) {
    throw new Error(`Invalid config file '${path}'. Expected a frontend section.`);
  }

  const frontend = (rawConfig as { frontend: unknown }).frontend;
  if (!frontend || typeof frontend !== "object") {
    throw new Error(`Invalid config file '${path}'. Expected frontend to be an object.`);
  }

  const frontendConfig = frontend as Record<string, unknown>;
  return {
    frontend: {
      host: assertString(frontendConfig.host, "frontend.host"),
      port: assertPort(frontendConfig.port, "frontend.port"),
      backend_proxy_url: assertString(frontendConfig.backend_proxy_url, "frontend.backend_proxy_url"),
    },
  };
}

export const appConfig = readConfig();
