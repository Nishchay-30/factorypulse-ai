"""
FactoryPulse AI - Industrial Dark Theme CSS & Styling Assets
"""

INDUSTRIAL_THEME_CSS = """
<style>
/* Main Dark Industrial Palette */
:root {
    --bg-dark: #0f141c;
    --card-bg: #18202c;
    --border-color: #273445;
    --accent-blue: #0088ff;
    --accent-cyan: #00d2ff;
    --status-normal: #00e676;
    --status-warning: #ffb300;
    --status-critical: #ff3d00;
    --text-primary: #f0f4f8;
    --text-muted: #8fa0b5;
}

/* Background overrides */
.stApp {
    background-color: var(--bg-dark);
    color: var(--text-primary);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

/* Header Banner */
.factory-header {
    background: linear-gradient(135deg, #131c28 0%, #1c2b3e 100%);
    border: 1px solid var(--border-color);
    border-radius: 10px;
    padding: 18px 24px;
    margin-bottom: 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
}

.factory-title {
    font-size: 24px;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: 0.5px;
    margin: 0;
}

.factory-subtitle {
    font-size: 13px;
    color: var(--accent-cyan);
    margin-top: 4px;
}

/* Metric / KPI Cards */
.kpi-card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 12px;
    transition: transform 0.2s ease, border-color 0.2s ease;
}

.kpi-card:hover {
    border-color: var(--accent-blue);
    transform: translateY(-2px);
}

.kpi-title {
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--text-muted);
    margin-bottom: 6px;
}

.kpi-value {
    font-size: 26px;
    font-weight: 700;
    color: #ffffff;
}

.kpi-subtext {
    font-size: 12px;
    margin-top: 4px;
}

/* Status Badges */
.badge-normal {
    background-color: rgba(0, 230, 118, 0.15);
    color: var(--status-normal);
    border: 1px solid rgba(0, 230, 118, 0.4);
    padding: 4px 10px;
    border-radius: 4px;
    font-weight: 600;
    font-size: 12px;
    display: inline-block;
}

.badge-warning {
    background-color: rgba(255, 179, 0, 0.15);
    color: var(--status-warning);
    border: 1px solid rgba(255, 179, 0, 0.4);
    padding: 4px 10px;
    border-radius: 4px;
    font-weight: 600;
    font-size: 12px;
    display: inline-block;
}

.badge-critical {
    background-color: rgba(255, 61, 0, 0.15);
    color: var(--status-critical);
    border: 1px solid rgba(255, 61, 0, 0.4);
    padding: 4px 10px;
    border-radius: 4px;
    font-weight: 600;
    font-size: 12px;
    display: inline-block;
}

/* Station Pipeline Cards */
.station-card {
    background: #141b24;
    border: 1px solid #222d3d;
    border-radius: 8px;
    padding: 16px;
    height: 100%;
}

.station-title {
    font-size: 16px;
    font-weight: 600;
    color: #e2e8f0;
    margin-bottom: 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

/* Queue Bar representation */
.queue-container {
    background: #0b0f14;
    border-radius: 4px;
    height: 18px;
    width: 100%;
    margin: 8px 0;
    overflow: hidden;
    border: 1px solid #1f2937;
}

.queue-fill {
    height: 100%;
    transition: width 0.3s ease;
}

/* Tables and Dataframes */
div[data-testid="stTable"], div[data-testid="stDataFrame"] {
    background-color: var(--card-bg);
    border-radius: 8px;
    border: 1px solid var(--border-color);
}
</style>
"""

