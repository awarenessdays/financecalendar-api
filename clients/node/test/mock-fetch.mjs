// Preload with `node --import ./test/mock-fetch.mjs ...` so child processes (CLI, MCP server) use fixtures.
import { installMockFetch } from "./fixtures.js";
installMockFetch();
