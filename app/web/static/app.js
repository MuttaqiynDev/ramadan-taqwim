/* ===== Ramazon Taqvimi – WebApp JavaScript ===== */

const tg = window.Telegram?.WebApp;
const initData = tg?.initData || "";

const API_BASE = "";  // Same origin

// DOM references
const $loading = document.getElementById("loading-screen");
const $error = document.getElementById("error-screen");
const $errorMsg = document.getElementById("error-message");
const $app = document.getElementById("app");

// Bugun tab elements
const $gregDate = document.getElementById("greg-date");
const $hijriDate = document.getElementById("hijri-date");
const $regionPill = document.getElementById("region-pill");
const $eventLabel = document.getElementById("event-label");
const $eventTime = document.getElementById("event-time");
const $remainingTime = document.getElementById("remaining-time");
const $ringProgress = document.getElementById("ring-progress");
const $saharlikArabic = document.getElementById("saharlik-arabic");
const $saharlikReading = document.getElementById("saharlik-reading");
const $iftorlikArabic = document.getElementById("iftorlik-arabic");
const $iftorlikReading = document.getElementById("iftorlik-reading");
const $reminderToggle = document.getElementById("reminder-toggle");
const $calendarContainer = document.getElementById("calendar-container");

// State
let todayData = null;
let remainingSeconds = 0;
let totalSeconds = 0;  // total duration of current period (for ring progress)
let countdownInterval = null;
let reminderEnabled = false;
let monthLoaded = false;

// ===== INITIALIZATION =====
document.addEventListener("DOMContentLoaded", async () => {
    if (tg) {
        tg.ready();
        tg.expand();
    }

    // Setup tabs
    document.querySelectorAll(".tab-btn").forEach(btn => {
        btn.addEventListener("click", () => switchTab(btn.dataset.tab));
    });

    // Reminder toggle
    $reminderToggle.addEventListener("click", toggleReminder);

    // Load today data
    await loadToday();
});

// ===== API HELPERS =====
async function apiFetch(path, options = {}) {
    const separator = path.includes("?") ? "&" : "?";
    const url = `${API_BASE}${path}${separator}initData=${encodeURIComponent(initData)}`;
    const resp = await fetch(url, options);
    if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: resp.statusText }));
        throw new Error(err.detail || "Server error");
    }
    return resp;
}

async function apiJSON(path) {
    const resp = await apiFetch(path);
    return resp.json();
}

// ===== LOAD TODAY =====
async function loadToday() {
    try {
        todayData = await apiJSON("/api/today");
        renderToday(todayData);
        showApp();
    } catch (e) {
        showError(e.message);
    }
}

function renderToday(data) {
    $gregDate.textContent = data.gregorian_date;
    $hijriDate.textContent = data.hijri_date;
    $regionPill.textContent = data.region_name;
    $eventLabel.textContent = data.next_event_name;
    $eventTime.textContent = data.next_event_time;

    // Reminder state
    reminderEnabled = data.reminder_enabled;
    updateReminderUI();

    // Duas
    if (data.duas?.saharlik) {
        $saharlikArabic.textContent = data.duas.saharlik.arabic || "";
        $saharlikReading.textContent = data.duas.saharlik.reading || "";
    }
    if (data.duas?.iftorlik) {
        $iftorlikArabic.textContent = data.duas.iftorlik.arabic || "";
        $iftorlikReading.textContent = data.duas.iftorlik.reading || "";
    }

    // Start countdown
    remainingSeconds = data.remaining_seconds || 0;

    // Calculate total duration for ring progress
    // total_seconds from API, or compute from suhoor/iftar window
    if (data.total_seconds) {
        totalSeconds = data.total_seconds;
    } else {
        // Estimate: parse suhoor & iftar times to get the window
        const [sh, sm] = (data.suhoor || "05:00").split(":").map(Number);
        const [ih, im] = (data.iftar || "18:00").split(":").map(Number);
        const suhoorMins = sh * 60 + sm;
        const iftarMins = ih * 60 + im;
        if (data.next_event_name === "Iftor") {
            // From suhoor to iftar
            totalSeconds = (iftarMins - suhoorMins) * 60;
        } else {
            // From iftar to next suhoor (~11 hours)
            totalSeconds = ((24 * 60 - iftarMins) + suhoorMins) * 60;
        }
    }
    if (totalSeconds <= 0) totalSeconds = remainingSeconds || 1;

    startCountdown();
}

// ===== COUNTDOWN =====
function startCountdown() {
    if (countdownInterval) clearInterval(countdownInterval);

    updateCountdownDisplay();
    countdownInterval = setInterval(() => {
        remainingSeconds--;
        if (remainingSeconds <= 0) {
            remainingSeconds = 0;
            clearInterval(countdownInterval);
            // Refresh data when event time passes
            setTimeout(() => loadToday(), 2000);
        }
        updateCountdownDisplay();
    }, 1000);
}

function updateCountdownDisplay() {
    const h = Math.floor(remainingSeconds / 3600);
    const m = Math.floor((remainingSeconds % 3600) / 60);
    const s = remainingSeconds % 60;

    const hStr = String(h).padStart(2, "0");
    const mStr = String(m).padStart(2, "0");
    const sStr = String(s).padStart(2, "0");

    $remainingTime.textContent = `- ${hStr}:${mStr}:${sStr}`;

    // Update ring progress — drains from full to empty as time passes
    const circumference = 2 * Math.PI * 52; // r=52
    const elapsed = totalSeconds - remainingSeconds;
    const fraction = Math.max(0, Math.min(1, remainingSeconds / totalSeconds));
    // strokeDashoffset = 0 means full ring, = circumference means empty
    const offset = circumference * (1 - fraction);
    $ringProgress.style.strokeDashoffset = offset;

    // Update the notch position on the ring
    const notch = document.querySelector('.ring-notch');
    if (notch) {
        // Angle: 0 = top (12 o'clock), goes clockwise
        // fraction=1 → top, fraction=0 → top (full circle consumed)
        const angle = (1 - fraction) * 360;
        const radians = (angle - 90) * Math.PI / 180;
        const cx = 60 + 52 * Math.cos(radians);
        const cy = 60 + 52 * Math.sin(radians);
        notch.setAttribute('cx', cx);
        notch.setAttribute('cy', cy);
    }
}

// ===== REMINDER TOGGLE =====
function updateReminderUI() {
    if (reminderEnabled) {
        $reminderToggle.classList.add("active");
    } else {
        $reminderToggle.classList.remove("active");
    }
}

async function toggleReminder() {
    reminderEnabled = !reminderEnabled;
    updateReminderUI();

    try {
        await fetch(`${API_BASE}/api/settings`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                initData: initData,
                reminder_enabled: reminderEnabled,
            }),
        });
    } catch (e) {
        // Revert on error
        reminderEnabled = !reminderEnabled;
        updateReminderUI();
        console.error("Failed to update reminder:", e);
    }
}

// ===== MONTHLY TAB =====
async function loadMonth() {
    if (monthLoaded) return;

    $calendarContainer.innerHTML = '<div class="calendar-loading"><div class="loading-spinner small"></div></div>';

    try {
        const data = await apiJSON("/api/month");
        renderMonth(data);
        monthLoaded = true;
    } catch (e) {
        $calendarContainer.innerHTML = `<p style="padding:20px;color:#999;text-align:center;">Xatolik: ${e.message}</p>`;
    }
}

function renderMonth(data) {
    if (data.rows && data.rows.length > 0) {
        // Render as table
        let html = '<table class="cal-table">';
        html += '<thead><tr><th>Kun</th><th>Sana</th><th>Hafta kuni</th><th>Saharlik</th><th>Iftorlik</th></tr></thead>';
        html += '<tbody>';

        const todayStr = new Date().toISOString().slice(0, 10);

        for (const row of data.rows) {
            const isToday = row.date === todayStr;
            html += `<tr class="${isToday ? 'today-row' : ''}">`;
            html += `<td>${row.day}</td>`;
            html += `<td>${row.date.slice(5)}</td>`;
            html += `<td>${row.weekday}</td>`;
            html += `<td>${row.suhoor}</td>`;
            html += `<td>${row.iftar}</td>`;
            html += '</tr>';
        }

        html += '</tbody></table>';
        $calendarContainer.innerHTML = html;
    } else {
        $calendarContainer.innerHTML = '<p style="padding:20px;color:#999;text-align:center;">Ma\'lumot topilmadi</p>';
    }
}

// ===== TAB SWITCHING =====
function switchTab(tabName) {
    // Update buttons
    document.querySelectorAll(".tab-btn").forEach(btn => {
        btn.classList.toggle("active", btn.dataset.tab === tabName);
    });

    // Update content
    document.querySelectorAll(".tab-content").forEach(tc => {
        tc.classList.toggle("active", tc.id === `tab-${tabName}`);
    });

    // Lazy-load month
    if (tabName === "oylik") {
        loadMonth();
    }
}

// ===== SHOW/HIDE STATES =====
function showApp() {
    $loading.classList.add("hidden");
    $error.classList.add("hidden");
    $app.classList.remove("hidden");
}

function showError(msg) {
    $loading.classList.add("hidden");
    $app.classList.add("hidden");
    $error.classList.remove("hidden");
    $errorMsg.textContent = msg || "Xatolik yuz berdi";
}
