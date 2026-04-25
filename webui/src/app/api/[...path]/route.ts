import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { NextRequest } from "next/server";

export const runtime = "nodejs";

function defaultConfigPath(): string {
  for (const candidate of ["config.yaml", "../config.yaml"]) {
    const resolved = resolve(candidate);
    if (existsSync(resolved)) {
      return resolved;
    }
  }

  return resolve("config.yaml");
}

function configValue(sectionName: string, fieldName: string): string {
  const configPath = defaultConfigPath();
  const configText = readFileSync(configPath, "utf8");
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

    const match = line.match(new RegExp(`^\\s{2}${fieldName}:\\s*["']?([^"'\\n#]+)["']?\\s*(?:#.*)?$`));
    if (match) {
      return match[1].trim();
    }
  }

  throw new Error(`Missing '${sectionName}.${fieldName}' in ${configPath}.`);
}

function backendUrl(path: string[]): string {
  const backendProxyTarget = configValue("frontend", "backend_proxy_url");
  const baseUrl = backendProxyTarget.replace(/\/$/, "");
  return `${baseUrl}/api/${path.map(encodeURIComponent).join("/")}`;
}

async function proxyRequest(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const targetUrl = new URL(backendUrl(path));
  targetUrl.search = request.nextUrl.search;

  const response = await fetch(targetUrl, {
    method: request.method,
    headers: request.headers,
    body: request.method === "GET" || request.method === "HEAD" ? undefined : request.body,
    duplex: "half",
  } as RequestInit);

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers,
  });
}

export const GET = proxyRequest;
export const POST = proxyRequest;
export const PUT = proxyRequest;
export const PATCH = proxyRequest;
export const DELETE = proxyRequest;
