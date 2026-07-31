import assert from "node:assert/strict";
import test from "node:test";

import { validateSimulationInputs, variableRate } from "../src/lib/validation.ts";
import { getSettings, saveSettings } from "../src/lib/api.ts";

function memoryStorage(): Storage {
  const values = new Map<string, string>();
  return {
    get length() { return values.size; },
    clear: () => values.clear(),
    getItem: (key) => values.get(key) ?? null,
    key: (index) => [...values.keys()][index] ?? null,
    removeItem: (key) => { values.delete(key); },
    setItem: (key, value) => { values.set(key, String(value)); },
  };
}

test("accepts decimal and percentage variable-cost rates", () => {
  assert.equal(variableRate("0.4"), 0.4);
  assert.equal(variableRate("40"), 0.4);
});

test("rejects invalid rates and fractional seats", () => {
  assert.throws(() => variableRate("100"), /0–1/);
  assert.throws(
    () => validateSimulationInputs({ avgTicket: "30", seatCount: "2.5", dailyFixedCost: "2000", variableCostRate: "40" }),
    /座位数必须是整数/,
  );
});

test("keeps blank optional assumptions undefined", () => {
  assert.deepEqual(
    validateSimulationInputs({ avgTicket: "", seatCount: "", dailyFixedCost: "", variableCostRate: "" }),
    { avg_ticket: undefined, seat_count: undefined, daily_fixed_cost: undefined, variable_cost_rate: undefined },
  );
});

test("keeps the API access token out of persistent local storage", () => {
  const localStorage = memoryStorage();
  const sessionStorage = memoryStorage();
  Object.defineProperty(globalThis, "window", {
    configurable: true,
    value: { localStorage, sessionStorage },
  });
  saveSettings({ apiEndpoint: "http://127.0.0.1:8000", analysisRadius: 800, theme: "dark", apiAccessToken: "secret" });
  assert.doesNotMatch(localStorage.getItem("restaurant-agent-settings-v1") || "", /secret/);
  assert.equal(getSettings().apiAccessToken, "secret");
});
