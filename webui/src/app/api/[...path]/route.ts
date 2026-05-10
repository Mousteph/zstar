import { NextRequest } from "next/server";

import { getFrontendRuntimeConfig } from "@/server/runtime-config.mjs";

export const runtime = "nodejs";

function backendUrl(path: string[]): string {
  const backendProxyTarget = getFrontendRuntimeConfig().backendProxyUrl;
  const baseUrl = backendProxyTarget.replace(/\/$/, "");
  return `${baseUrl}/api/${path.map(encodeURIComponent).join("/")}`;
}

function buildProxyHeaders(request: NextRequest): Headers {
  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  const accept = request.headers.get("accept");
  const requestId = request.headers.get("x-request-id");

  if (contentType) {
    headers.set("content-type", contentType);
  }
  if (accept) {
    headers.set("accept", accept);
  }
  if (requestId) {
    headers.set("x-request-id", requestId);
  }

  return headers;
}

function buildResponseHeaders(response: Response): Headers {
  const headers = new Headers();
  const contentType = response.headers.get("content-type");
  const requestId = response.headers.get("x-request-id");

  if (contentType) {
    headers.set("content-type", contentType);
  }
  if (requestId) {
    headers.set("x-request-id", requestId);
  }

  return headers;
}

async function proxyRequest(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const targetUrl = new URL(backendUrl(path));
  targetUrl.search = request.nextUrl.search;

  let response: Response;
  try {
    response = await fetch(targetUrl, {
      method: request.method,
      headers: buildProxyHeaders(request),
      body: request.method === "GET" || request.method === "HEAD" ? undefined : request.body,
      duplex: "half",
    } as RequestInit);
  } catch {
    return Response.json(
      { detail: "Backend is unavailable. Please check that the ZStar API is running." },
      { status: 502 },
    );
  }

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: buildResponseHeaders(response),
  });
}

export const GET = proxyRequest;
export const POST = proxyRequest;
export const PUT = proxyRequest;
export const PATCH = proxyRequest;
export const DELETE = proxyRequest;
