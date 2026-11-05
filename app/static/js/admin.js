const message = document.getElementById("admin-message");
const tableBody = document.getElementById("activity-table-body");

function setText(id, value) {
    document.getElementById(id).textContent = value;
}

async function loadOverview() {
    try {
        const response = await fetch("/admin/overview", {
            credentials: "same-origin"
        });

        if (response.status === 401 || response.status === 403) {
            window.location.href = "/login";
            return;
        }

        if (!response.ok) {
            throw new Error("Could not load dashboard statistics.");
        }

        const data = await response.json();

        setText("total-users", data.total_users);
        setText("total-documents", data.total_documents);
        setText("total-events", data.total_events);
        setText("successful-events", data.successful_events);
        setText("denied-events", data.denied_events);
    } catch (error) {
        message.textContent = error.message;
    }
}

async function loadActivity() {
    message.textContent = "Loading recent activity...";
    tableBody.replaceChildren();

    try {
        const response = await fetch("/admin/activity?limit=10", {
            credentials: "same-origin"
        });

        if (response.status === 401 || response.status === 403) {
            window.location.href = "/login";
            return;
        }

        if (!response.ok) {
            throw new Error("Could not load activity records.");
        }

        const data = await response.json();

        if (!data.items || data.items.length === 0) {
            message.textContent = "No activity records found.";
            const row = document.createElement("tr");
            const cell = document.createElement("td");
            cell.colSpan = 6;
            cell.textContent = "No records available.";
            row.appendChild(cell);
            tableBody.appendChild(row);
            return;
        }

        data.items.forEach(event => {
            const row = document.createElement("tr");

            const values = [
                event.id,
                event.action,
                event.actor_user_id ?? "System",
                event.document_id ?? "—"
            ];

            values.forEach(value => {
                const cell = document.createElement("td");
                cell.textContent = String(value);
                row.appendChild(cell);
            });

            const outcomeCell = document.createElement("td");
            const badge = document.createElement("span");
            badge.className = `admin-outcome ${event.outcome === "success" ? "success" : "denied"}`;
            badge.textContent = event.outcome;
            outcomeCell.appendChild(badge);
            row.appendChild(outcomeCell);

            const dateCell = document.createElement("td");
            dateCell.textContent = event.created_at
                ? new Date(event.created_at).toLocaleString()
                : "—";
            row.appendChild(dateCell);

            tableBody.appendChild(row);
        });

        message.textContent = `Showing ${data.items.length} recent events.`;
    } catch (error) {
        message.textContent = error.message;
        const row = document.createElement("tr");
        const cell = document.createElement("td");
        cell.colSpan = 6;
        cell.textContent = "Unable to load activity.";
        row.appendChild(cell);
        tableBody.appendChild(row);
    }
}

async function refreshDashboard() {
    await Promise.all([loadOverview(), loadActivity()]);
}

document.getElementById("refresh-button")
    .addEventListener("click", refreshDashboard);

document.getElementById("logout-button")
    .addEventListener("click", async () => {
        try {
            const response = await fetch("/auth/logout", {
                method: "POST",
                credentials: "same-origin"
            });

            if (response.ok) {
                window.location.href = "/login";
            } else {
                message.textContent = "Logout failed. Please try again.";
            }
        } catch {
            message.textContent = "Could not connect to the server.";
        }
    });

refreshDashboard();
