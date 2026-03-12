import json
from datetime import datetime, timedelta

from flask import jsonify, render_template_string

from database import Lead, Session


def create_dashboard(app):
    @app.route("/dashboard", methods=["GET"])
    def dashboard():
        db_session = Session()
        total_leads = db_session.query(Lead).count()
        new_leads = db_session.query(Lead).filter_by(status="new").count()
        approved = db_session.query(Lead).filter_by(status="approved").count()
        interested = db_session.query(Lead).filter_by(status="interested").count()
        enrolled = db_session.query(Lead).filter_by(status="enrolled").count()
        hot_leads = db_session.query(Lead).filter(Lead.score >= 70).count()
        week_ago = datetime.now() - timedelta(days=7)
        leads_this_week = (
            db_session.query(Lead).filter(Lead.created_at >= week_ago).count()
        )
        recent = db_session.query(Lead).order_by(Lead.created_at.desc()).limit(8).all()
        db_session.close()

        rows = ""
        for lead in recent:
            score_class = (
                "high"
                if (lead.score or 0) >= 70
                else "mid" if (lead.score or 0) >= 40 else "low"
            )
            rows += f"""
            <tr>
                <td>
                    <strong>{lead.name}</strong><br>
                    <span class="meta">{lead.email or 'No email'} | {lead.phone or 'No phone'}</span>
                </td>
                <td>{lead.sport or '?'}</td>
                <td class="{score_class}">{lead.score or 0}</td>
                <td><span class="tag">{lead.status}</span></td>
                <td>{lead.goal or 'General interest'}</td>
                <td>{lead.created_at.strftime('%Y-%m-%d')}</td>
            </tr>
            """

        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>LeadFlow AI Dashboard</title>
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
            <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;700;800&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">
            <style>
                body {{
                    margin: 0;
                    font-family: "Manrope", sans-serif;
                    color: #132235;
                    background: linear-gradient(135deg, #fffef9, #f2f8ff 40%, #eef9f4);
                }}
                .wrap {{ max-width: 1200px; margin: 0 auto; padding: 24px; }}
                .hero {{
                    padding: 28px;
                    border-radius: 26px;
                    color: white;
                    background: linear-gradient(135deg, #173764, #315efb);
                    box-shadow: 0 18px 40px rgba(21, 35, 52, 0.14);
                }}
                .hero h1 {{
                    margin: 0;
                    font-family: "Space Grotesk", sans-serif;
                    font-size: clamp(2rem, 3vw, 3rem);
                }}
                .hero p {{ margin: 12px 0 0; color: rgba(255,255,255,0.84); max-width: 720px; }}
                .links {{ margin-top: 20px; display: flex; gap: 10px; flex-wrap: wrap; }}
                .links a {{
                    color: white;
                    text-decoration: none;
                    padding: 10px 14px;
                    border-radius: 999px;
                    background: rgba(255,255,255,0.14);
                }}
                .stats {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
                    gap: 16px;
                    margin-top: 22px;
                }}
                .card {{
                    background: rgba(255,255,255,0.82);
                    border: 1px solid rgba(255,255,255,0.9);
                    border-radius: 22px;
                    padding: 20px;
                    box-shadow: 0 14px 30px rgba(21, 35, 52, 0.09);
                    backdrop-filter: blur(14px);
                }}
                .kicker {{
                    color: #5e7288;
                    font-size: 0.84rem;
                    text-transform: uppercase;
                    letter-spacing: 0.08em;
                }}
                .value {{
                    margin-top: 8px;
                    font-size: 2rem;
                    font-weight: 800;
                }}
                .layout {{
                    display: grid;
                    grid-template-columns: 1.7fr 1fr;
                    gap: 18px;
                    margin-top: 22px;
                }}
                .panel h2 {{
                    margin: 0 0 6px;
                    font-family: "Space Grotesk", sans-serif;
                }}
                .sub {{ color: #5e7288; margin-bottom: 18px; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 12px 8px; border-bottom: 1px solid rgba(19,34,53,0.08); text-align: left; }}
                th {{ color: #5e7288; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.08em; }}
                .meta {{ color: #5e7288; font-size: 0.82rem; }}
                .tag {{
                    display: inline-block;
                    padding: 7px 11px;
                    border-radius: 999px;
                    background: rgba(49,94,251,0.1);
                    font-weight: 700;
                    font-size: 0.82rem;
                }}
                .high {{ color: #1b8f69; font-weight: 800; }}
                .mid {{ color: #d48919; font-weight: 800; }}
                .low {{ color: #c0443f; font-weight: 800; }}
                .focus {{
                    display: grid;
                    gap: 14px;
                }}
                .focus-item {{
                    padding: 16px;
                    border-radius: 18px;
                    background: rgba(255,255,255,0.92);
                    border: 1px solid rgba(19,34,53,0.06);
                }}
                .focus-item strong {{ display: block; font-size: 1.2rem; margin-top: 6px; }}
                @media (max-width: 900px) {{
                    .layout {{ grid-template-columns: 1fr; }}
                }}
            </style>
        </head>
        <body>
            <div class="wrap">
                <section class="hero">
                    <h1>LeadFlow AI Dashboard</h1>
                    <p>Track pipeline movement, spot high-intent leads quickly, and keep coaches focused on the right conversations.</p>
                    <div class="links">
                        <a href="/dashboard/analytics">Open Analytics</a>
                        <a href="/api/stats">JSON Stats</a>
                    </div>
                </section>

                <section class="stats">
                    <article class="card"><div class="kicker">Total Leads</div><div class="value">{total_leads}</div></article>
                    <article class="card"><div class="kicker">New Queue</div><div class="value">{new_leads}</div></article>
                    <article class="card"><div class="kicker">Approved</div><div class="value">{approved}</div></article>
                    <article class="card"><div class="kicker">Interested</div><div class="value">{interested}</div></article>
                    <article class="card"><div class="kicker">Enrolled</div><div class="value">{enrolled}</div></article>
                    <article class="card"><div class="kicker">Hot Leads</div><div class="value">{hot_leads}</div></article>
                    <article class="card"><div class="kicker">This Week</div><div class="value">{leads_this_week}</div></article>
                </section>

                <section class="layout">
                    <article class="card panel">
                        <h2>Recent Leads</h2>
                        <div class="sub">Latest captured prospects, live from your SQLite pipeline.</div>
                        {"<div class='sub'>No leads yet. Send a webhook lead to populate the dashboard.</div>" if not recent else f"<table><tr><th>Lead</th><th>Sport</th><th>Score</th><th>Status</th><th>Intent</th><th>Created</th></tr>{rows}</table>"}
                    </article>

                    <aside class="focus">
                        <article class="card">
                            <div class="kicker">Hot Lead Ratio</div>
                            <div class="value">{round((hot_leads / total_leads) * 100, 1) if total_leads else 0}%</div>
                            <div class="sub">Share of leads scoring 70 or above.</div>
                        </article>
                        <article class="card">
                            <div class="kicker">Approval Rate</div>
                            <div class="value">{round((approved / total_leads) * 100, 1) if total_leads else 0}%</div>
                            <div class="sub">How much of the total pipeline has moved into outreach.</div>
                        </article>
                        <article class="card">
                            <div class="kicker">Coach Focus</div>
                            <div class="focus-item">
                                <span class="kicker">Top Priority</span>
                                <strong>{recent[0].name if recent else 'No leads yet'}</strong>
                                <span class="meta">{recent[0].sport or 'Unknown sport'} | score {recent[0].score or 0 if recent else 0}</span>
                            </div>
                            <div class="focus-item">
                                <span class="kicker">Queue Risk</span>
                                <strong>{new_leads}</strong>
                                <span class="meta">Leads waiting for approval</span>
                            </div>
                        </article>
                    </aside>
                </section>
            </div>
        </body>
        </html>
        """
        return render_template_string(html)

    @app.route("/api/stats", methods=["GET"])
    def api_stats():
        db_session = Session()
        week_ago = datetime.now() - timedelta(days=7)
        stats = {
            "total": db_session.query(Lead).count(),
            "new": db_session.query(Lead).filter_by(status="new").count(),
            "approved": db_session.query(Lead).filter_by(status="approved").count(),
            "interested": db_session.query(Lead).filter_by(status="interested").count(),
            "enrolled": db_session.query(Lead).filter_by(status="enrolled").count(),
            "hot": db_session.query(Lead).filter(Lead.score >= 70).count(),
            "this_week": db_session.query(Lead).filter(Lead.created_at >= week_ago).count(),
            "conversion_rate": 0,
        }
        if stats["approved"] > 0:
            stats["conversion_rate"] = round(
                (stats["enrolled"] / stats["approved"]) * 100, 1
            )
        db_session.close()
        return jsonify(stats)

    @app.route("/dashboard/analytics", methods=["GET"])
    def analytics():
        db_session = Session()
        stages = ["new", "approved", "interested", "scheduled", "enrolled"]
        funnel = [
            {"stage": stage.title(), "count": db_session.query(Lead).filter_by(status=stage).count()}
            for stage in stages
        ]

        sports = {}
        sources = {}
        scores = []
        for lead in db_session.query(Lead).all():
            if lead.sport:
                sports[lead.sport] = sports.get(lead.sport, 0) + 1
            source = lead.source or "website"
            sources[source] = sources.get(source, 0) + 1
            scores.append(lead.score or 0)
        db_session.close()

        avg_score = round(sum(scores) / len(scores), 1) if scores else 0

        return render_template_string(
            f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>LeadFlow AI Analytics</title>
                <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
                <link rel="preconnect" href="https://fonts.googleapis.com">
                <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
                <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;700;800&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">
                <style>
                    body {{ margin: 0; font-family: "Manrope", sans-serif; color: #132235; background: linear-gradient(135deg, #fffef9, #f2f8ff 40%, #eef9f4); }}
                    .wrap {{ max-width: 1200px; margin: 0 auto; padding: 24px; }}
                    .hero {{ padding: 28px; border-radius: 26px; color: white; background: linear-gradient(135deg, #173764, #315efb); box-shadow: 0 18px 40px rgba(21, 35, 52, 0.14); display:flex; justify-content:space-between; gap:16px; align-items:end; }}
                    .hero h1 {{ margin: 0; font-family: "Space Grotesk", sans-serif; font-size: clamp(2rem, 3vw, 3rem); }}
                    .hero p {{ margin: 12px 0 0; color: rgba(255,255,255,0.84); }}
                    .hero a {{ color:white; text-decoration:none; padding:10px 14px; border-radius:999px; background:rgba(255,255,255,0.14); }}
                    .stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:16px; margin:22px 0; }}
                    .card {{ background: rgba(255,255,255,0.84); border:1px solid rgba(255,255,255,0.9); border-radius:22px; padding:20px; box-shadow:0 14px 30px rgba(21,35,52,0.09); }}
                    .kicker {{ color:#5e7288; font-size:0.84rem; text-transform:uppercase; letter-spacing:0.08em; }}
                    .value {{ margin-top:8px; font-size:2rem; font-weight:800; }}
                    .charts {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; }}
                    .wide {{ grid-column:1 / -1; }}
                    h3 {{ margin:0 0 8px; font-family:"Space Grotesk", sans-serif; }}
                    .sub {{ color:#5e7288; margin-bottom:16px; }}
                    @media (max-width:900px) {{ .charts {{ grid-template-columns:1fr; }} .hero {{ flex-direction:column; align-items:start; }} }}
                </style>
            </head>
            <body>
                <div class="wrap">
                    <section class="hero">
                        <div>
                            <h1>LeadFlow Analytics</h1>
                            <p>Understand where leads come from, how they move through the funnel, and where coaches should focus next.</p>
                        </div>
                        <a href="/dashboard">Back to Dashboard</a>
                    </section>
                    <section class="stats">
                        <article class="card"><div class="kicker">Average Lead Score</div><div class="value">{avg_score}</div></article>
                        <article class="card"><div class="kicker">Tracked Stages</div><div class="value">{len(funnel)}</div></article>
                        <article class="card"><div class="kicker">Sports Segments</div><div class="value">{len(sports)}</div></article>
                        <article class="card"><div class="kicker">Lead Sources</div><div class="value">{len(sources)}</div></article>
                    </section>
                    <section class="charts">
                        <article class="card">
                            <h3>Conversion Funnel</h3>
                            <div class="sub">See how leads progress from intake to enrollment-focused stages.</div>
                            <canvas id="funnelChart"></canvas>
                        </article>
                        <article class="card">
                            <h3>Leads by Sport</h3>
                            <div class="sub">Quick view of demand distribution across programs.</div>
                            <canvas id="sportsChart"></canvas>
                        </article>
                        <article class="card wide">
                            <h3>Lead Sources</h3>
                            <div class="sub">Understand which channels are feeding the pipeline.</div>
                            <canvas id="sourcesChart"></canvas>
                        </article>
                    </section>
                </div>
                <script>
                    const funnelData = {json.dumps(funnel)};
                    const sportsData = {json.dumps(sports)};
                    const sourcesData = {json.dumps(sources)};
                    new Chart(document.getElementById('funnelChart'), {{
                        type: 'bar',
                        data: {{
                            labels: funnelData.map(d => d.stage),
                            datasets: [{{ label: 'Leads', data: funnelData.map(d => d.count), backgroundColor: ['#315efb','#0f9d7a','#ff8b5e','#7d62ff','#ff5c58'], borderRadius: 12 }}]
                        }},
                        options: {{ plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ grid: {{ display: false }} }}, y: {{ beginAtZero: true }} }} }}
                    }});
                    new Chart(document.getElementById('sportsChart'), {{
                        type: 'pie',
                        data: {{ labels: Object.keys(sportsData), datasets: [{{ data: Object.values(sportsData), backgroundColor: ['#315efb','#0f9d7a','#ff8b5e','#7d62ff','#ff5c58','#f5c451'] }}] }}
                    }});
                    new Chart(document.getElementById('sourcesChart'), {{
                        type: 'doughnut',
                        data: {{ labels: Object.keys(sourcesData), datasets: [{{ data: Object.values(sourcesData), backgroundColor: ['#315efb','#0f9d7a','#ff8b5e','#7d62ff','#ff5c58','#f5c451'] }}] }}
                    }});
                </script>
            </body>
            </html>
            """
        )
