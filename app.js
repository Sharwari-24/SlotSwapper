const API_URL = "http://127.0.0.1:8000"; // backend running on uvicorn
let token = localStorage.getItem("token");

// Helper: set auth header
function authHeaders() {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

// ========== AUTH ==========
async function signup() {
  const name = document.getElementById("signup-name").value;
  const email = document.getElementById("signup-email").value;
  const password = document.getElementById("signup-password").value;

  const res = await fetch(`${API_URL}/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, email, password }),
  });

  if (res.ok) {
    alert("Signup successful! You can now log in.");
  } else {
    const msg = await res.text();
    alert("Signup failed: " + msg);
  }
}

async function login() {
  const email = document.getElementById("login-email").value;
  const password = document.getElementById("login-password").value;

  const res = await fetch(`${API_URL}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ username: email, password }),
  });

  if (res.ok) {
    const data = await res.json();
    token = data.access_token;
    localStorage.setItem("token", token);
    showDashboard();
  } else {
    const msg = await res.text();
    alert("Login failed: " + msg);
  }
}


function logout() {
  localStorage.removeItem("token");
  token = null;
  document.getElementById("dashboard").style.display = "none";
  document.getElementById("auth-section").style.display = "block";
}

// ========== DASHBOARD ==========
async function showDashboard() {
  document.getElementById("auth-section").style.display = "none";
  document.getElementById("dashboard").style.display = "block";
  await loadMyEvents();
  await loadSwappableEvents();
  await loadSwapRequests(); 
}

// Create new event
async function createMyEvent() {
  const title = document.getElementById("title").value;
  const start = document.getElementById("start").value;
  const end = document.getElementById("end").value;

  const token = localStorage.getItem("token"); // get JWT from login

  const response = await fetch("http://127.0.0.1:8000/events", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`, // ✅ send the token
    },
    body: JSON.stringify({
      title: title,
      start_time: start,
      end_time: end,
      status: "BUSY", // optional but sometimes required
    }),
  });

  if (response.ok) {
    alert("Event created!");
  } else {
    const data = await response.json();
    alert("Error creating event: " + (data.detail || response.status));
  }
}

      

// Load your events
// Load swappable events (others)
async function loadMyEvents() {
  const res = await fetch(`${API_URL}/events`, { headers: authHeaders() });
  const container = document.getElementById("my-events");
  container.innerHTML = "";

  console.log("Response status:", res.status);
  const text = await res.text();
  console.log("Raw response:", text);

  if (res.ok) {
    const events = JSON.parse(text);
    events.forEach((e) => {
      const div = document.createElement("div");
      div.innerHTML = `
        <b>${e.title}</b> (${e.status})
        <button onclick="makeSwappable(${e.id})">Make Swappable</button>
      `;
      container.appendChild(div);
    });
  } else {
    container.innerHTML = "<p>Error loading events</p>";
  }
}


  

// Make event swappable
async function makeSwappable(id) {
  const res = await fetch(`${API_URL}/events/${id}?status=SWAPPABLE`, {
  method: "PATCH",
  headers: authHeaders(),
});

  if (res.ok) {
    alert("Marked as SWAPPABLE");
    loadMyEvents();
    loadSwappableEvents();
  }
}

// Load swappable events (others)
async function loadSwappableEvents() {
  const res = await fetch(`${API_URL}/swappable-slots`, {
    headers: authHeaders(),
  });
  const container = document.getElementById("swappable-events");
  container.innerHTML = "";

  if (res.ok) {
    const events = await res.json();
    events.forEach((e) => {
      const div = document.createElement("div");
      div.innerHTML = `
        <b>${e.title}</b> (${e.status}) — User ${e.user_id}
        <button onclick="requestSwap(${e.id})">Request Swap</button>
      `;
      container.appendChild(div);
    });
  }
}

// Request a swap
async function requestSwap(theirSlotId) {
  const mySlotId = prompt("Enter your swappable event ID to offer in swap:");
  if (!mySlotId) return;

  const res = await fetch(`${API_URL}/swap-request`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({
      my_slot_id: parseInt(mySlotId),
      their_slot_id: parseInt(theirSlotId),
    }),
  });

  if (res.ok) {
    alert("Swap request sent!");
  } else {
    alert("Failed to send swap request");
  }
}

// Auto-login if token exists
if (token) showDashboard();
// Load incoming and outgoing swap requests
async function loadSwapRequests() {
  // Incoming
  const incomingRes = await fetch(`${API_URL}/swap/incoming`, { headers: authHeaders() });
  const incomingContainer = document.getElementById("incoming-requests");
  incomingContainer.innerHTML = "";

  if (incomingRes.ok) {
    const incoming = await incomingRes.json();
    incoming.forEach(req => {
      const div = document.createElement("div");
      div.innerHTML = `
        <b>Swap #${req.id}</b> — Offer from User ${req.requester_id}<br>
        My Event: ${req.responder_event_id}, Their Event: ${req.requester_event_id}<br>
        Status: ${req.status}<br>
        <button onclick="respondSwap(${req.id}, true)">Accept</button>
        <button onclick="respondSwap(${req.id}, false)">Reject</button>
      `;
      incomingContainer.appendChild(div);
    });
  }

  // Outgoing
  const outgoingRes = await fetch(`${API_URL}/swap/outgoing`, { headers: authHeaders() });
  const outgoingContainer = document.getElementById("outgoing-requests");
  outgoingContainer.innerHTML = "";

  if (outgoingRes.ok) {
    const outgoing = await outgoingRes.json();
    outgoing.forEach(req => {
      const div = document.createElement("div");
      div.innerHTML = `
        <b>Swap #${req.id}</b> — To User ${req.responder_id}<br>
        Offered: ${req.requester_event_id} ↔ ${req.responder_event_id}<br>
        Status: ${req.status}
      `;
      outgoingContainer.appendChild(div);
    });
  }
}

// Respond to a swap request
async function respondSwap(swapId, accept) {
  const res = await fetch(`${API_URL}/swap/respond/${swapId}`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ accept }),
  });

  if (res.ok) {
    alert("Response submitted!");
    loadSwapRequests();
    loadMyEvents();
  } else {
    alert("Failed to respond to swap");
  }
}
