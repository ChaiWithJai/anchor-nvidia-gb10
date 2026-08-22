(() => {
  const clientId = sessionStorage.anchorGoalClientId
    || (sessionStorage.anchorGoalClientId = crypto.randomUUID());
  const surface = location.pathname === "/patient" ? "patient-call" : "clinic-console";
  const payload = connected => JSON.stringify({client_id: clientId, surface, connected});
  const heartbeat = (connected = true) => {
    const body = payload(connected);
    if (!connected && navigator.sendBeacon) {
      navigator.sendBeacon(
        "/api/goal/heartbeat",
        new Blob([body], {type: "application/json"}),
      );
      return;
    }
    fetch("/api/goal/heartbeat", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body,
      keepalive: true,
    }).catch(() => {});
  };
  heartbeat();
  setInterval(heartbeat, 5000);
  addEventListener("visibilitychange", () => heartbeat());
  addEventListener("beforeunload", () => heartbeat(false));
})();
