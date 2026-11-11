
import React, { useEffect, useMemo, useState } from 'react';
import { request, token, API } from './api';

import {
  Activity, BriefcaseBusiness, ChartNoAxesCombined, Search,
  Users, Moon, Sun, LogOut, Upload, Sparkles, ShieldCheck,
  ArrowUpRight, Database, Bell, Menu, X, Code2, Globe2,
  TrendingUp, FileText
} from 'lucide-react';

import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from 'recharts';


const demo = {
  total_jobs: 0,
  total_skills: 0,
  top_skills: [],
  countries: [],
  industries: []
};


function App() {
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('user'));
    } catch {
      return null;
    }
  });

  const [page, setPage] = useState('Overview');
  const [dark, setDark] = useState(true);

  const [stats, setStats] = useState(demo);
  const [jobs, setJobs] = useState([]);
  const [experienceData, setExperienceData] = useState([]);
  const [topSkills, setTopSkills] = useState([]);

  const [query, setQuery] = useState('');
  const [skill, setSkill] = useState('Python');
  const [detail, setDetail] = useState(null);

  const [compare, setCompare] = useState('Python, Java');
  const [comp, setComp] = useState(null);

  const [profile, setProfile] = useState({
    skills: '',
    target_role: ''
  });

  const [recs, setRecs] = useState(null);
  const [gap, setGap] = useState(null);
  const [admin, setAdmin] = useState(null);

  const [msg, setMsg] = useState('');
  const [authMode, setAuthMode] = useState('login');

  const [auth, setAuth] = useState({
    name: '',
    email: 'student@example.com',
    password: 'Student123!',
    role: 'student'
  });

  const [loading, setLoading] = useState(false);

  const headers = useMemo(() => ({}), []);


  // Load dashboard data from backend
  async function load() {
  try {
    const [
      overview,
      jobData,
      experience,
      skills
    ] = await Promise.all([
      request('/analytics/overview'),
      request('/jobs?limit=30'),
      request('/analytics/experience'),
      request('/analytics/top-skills?limit=20')
    ]);

    setStats(overview);
    setJobs(jobData.items || []);
    setExperienceData(experience || []);
    setTopSkills(skills || []);
    setMsg('');

  } catch (e) {
    setMsg(e.message);
  }
}


  useEffect(() => {
    load();
  }, []);


  useEffect(() => {
    if (user) {
      setProfile({
        skills: user.skills || '',
        target_role: user.target_role || ''
      });
    }
  }, [user]);


  useEffect(() => {
    document.documentElement.dataset.theme = dark ? 'dark' : 'light';
  }, [dark]);


  async function submitAuth(e) {
    e.preventDefault();
    setLoading(true);
    setMsg('');

    try {
      const data = await request(
        authMode === 'login' ? '/auth/login' : '/auth/register',
        {
          method: 'POST',
          body: JSON.stringify(auth)
        }
      );

      localStorage.setItem('token', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));

      setUser(data.user);
      setMsg('Welcome back!');

      await load();

    } catch (e) {
      setMsg(e.message);
    } finally {
      setLoading(false);
    }
  }


  function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');

    setUser(null);
    setPage('Overview');
  }


  async function searchJobs(e) {
    e?.preventDefault();

    try {
      const data = await request(
        `/jobs?q=${encodeURIComponent(query)}&limit=100`
      );

      setJobs(data.items);
      setPage('Jobs');

    } catch (e) {
      setMsg(e.message);
    }
  }


  async function inspectSkill() {
    try {
      setDetail(
        await request(`/analytics/skills/${encodeURIComponent(skill)}`)
      );
    } catch (e) {
      setDetail({ error: e.message });
    }
  }


  async function compareSkills() {
    try {
      setComp(
        await request('/analytics/compare', {
          method: 'POST',
          body: JSON.stringify({
            skills: compare.split(',').map(s => s.trim()).filter(Boolean)
          })
        })
      );
    } catch (e) {
      setMsg(e.message);
    }
  }


  async function saveProfile(e) {
    e.preventDefault();

    try {
      await request('/profile', {
        method: 'PUT',
        body: JSON.stringify(profile)
      });

      setMsg('Profile saved');

    } catch (e) {
      setMsg(e.message);
    }
  }


  async function loadRecommendations() {
    try {
      setRecs(await request('/recommendations'));
      setGap(await request('/recommendations/skill-gap'));
    } catch (e) {
      setMsg(e.message);
    }
  }


  async function loadAdmin() {
    try {
      setAdmin(await request('/admin/overview'));
    } catch (e) {
      setMsg(e.message);
    }
  }


  async function uploadResume(e) {
    const file = e.target.files?.[0];

    if (!file) return;

    const fd = new FormData();
    fd.append('file', file);

    try {
      const data = await request('/resumes/analyze', {
        method: 'POST',
        body: fd
      });

      setProfile(p => ({
        ...p,
        skills: [
          ...new Set([
            ...p.skills.split(',').map(x => x.trim()).filter(Boolean),
            ...data.extracted_skills
          ])
        ].join(', ')
      }));

      setMsg(
        `Extracted ${data.extracted_skills.length} skills. Save your profile to keep them.`
      );

    } catch (e) {
      setMsg(e.message);
    }
  }


  async function uploadCsv(e) {
    const file = e.target.files?.[0];

    if (!file) return;

    const fd = new FormData();
    fd.append('file', file);

    try {
      const data = await request('/admin/ingest-csv', {
        method: 'POST',
        body: fd
      });

      setMsg(`${data.records_added} jobs imported`);

      await load();
      await loadAdmin();

    } catch (e) {
      setMsg(e.message);
    }
  }


  const nav = [
    'Overview',
    'Jobs',
    'Skill Insights',
    'Compare Skills',
    ...(user?.role === 'student'
      ? ['My Profile', 'Recommendations']
      : []),
    ...(user?.role === 'admin' ? ['Admin'] : [])
  ];


  function go(p) {
    setPage(p);
    setMsg('');

    if (p === 'Recommendations') loadRecommendations();
    if (p === 'Admin') loadAdmin();
  }


  return (
    <div className="app-shell">

      {/* Sidebar */}
      <aside className="sidebar">

        <div className="brand">
          <div className="brand-icon">
            <Activity size={21} />
          </div>

          <div>
            <b>SkillScope</b>
            <small>JOB MARKET INTELLIGENCE</small>
          </div>
        </div>

        <div className="workspace-label">WORKSPACE</div>

        {nav.map((n, i) => (
          <button
            key={n}
            className={`nav-item ${page === n ? 'active' : ''}`}
            onClick={() => go(n)}
          >
            {[
              <ChartNoAxesCombined />,
              <BriefcaseBusiness />,
              <TrendingUp />,
              <Code2 />,
              <Users />,
              <Sparkles />,
              <ShieldCheck />
            ][
              ['Overview', 'Jobs', 'Skill Insights', 'Compare Skills',
                'My Profile', 'Recommendations', 'Admin'].indexOf(n)
            ] || <Activity />}

            <span>{n}</span>

            {n === 'Overview' && <i />}
          </button>
        ))}


        <div className="sidebar-bottom">

          <div className="source-card">
            <Database size={17} />
            <b>Data workspace</b>
            <span>{stats.total_jobs.toLocaleString()} postings indexed</span>
            <small>Insights update as data is added.</small>
          </div>

          <div className="user-mini">
            <div className="avatar">
              {user?.name?.[0] || 'G'}
            </div>

            <div className="user-label">
              <b>{user?.name || 'Guest explorer'}</b>
              <small>{user?.role || 'Public access'}</small>
            </div>

            {user && (
              <button
                className="icon-btn"
                onClick={logout}
                title="Logout"
              >
                <LogOut size={16} />
              </button>
            )}
          </div>

        </div>
      </aside>


      {/* Main content */}
      <main className="main-area">

        <header className="topbar">

          <div className="mobile-brand">
            <Activity /> SkillScope
          </div>

          <div className="crumb">
            Workspace <span>/</span> <b>{page}</b>
          </div>

          <div className="top-actions">

            <span className="live-dot">● Data insights</span>

            <button
              className="icon-btn"
              onClick={() => setDark(!dark)}
              title="Toggle theme"
            >
              {dark ? <Sun size={18} /> : <Moon size={18} />}
            </button>

            {user ? (
              <div className="top-user">
                {user.name}
                <span>{user.role}</span>
              </div>
            ) : (
              <button
                className="btn btn-primary btn-small"
                onClick={() =>
                  document.getElementById('auth')?.scrollIntoView({
                    behavior: 'smooth'
                  })
                }
              >
                Sign in
              </button>
            )}

          </div>
        </header>


        <div className="content">

          {msg && (
            <div className="toast" onClick={() => setMsg('')}>
              {msg}
              <button>×</button>
            </div>
          )}


          {/* Welcome banner */}
          {!user && (
            <section className="welcome-banner">

              <div>
                <span className="eyebrow">
                  <Sparkles size={14} />
                  AI-POWERED MARKET INTELLIGENCE
                </span>

                <h1>
                  Understand the market.
                  <br />
                  <em>Build what’s next.</em>
                </h1>

                <p>
                  Explore real job data, discover in-demand skills
                  and make confident career decisions.
                </p>
              </div>

              <div className="banner-art">
                <div className="orbit orbit-one" />
                <div className="orbit orbit-two" />

                <div className="orb-core">
                  <Activity size={36} />
                </div>

                <span className="float-tag tag-a">
                  Skill demand ↗
                </span>

                <span className="float-tag tag-b">
                  Market signals
                </span>
              </div>

            </section>
          )}


          {/* OVERVIEW */}
          {page === 'Overview' && (
            <>

              <div className="page-heading">

                <div>
                  <div className="eyebrow">
                    MARKET PULSE / OVERVIEW
                  </div>

                  <h1>Market overview</h1>

                  <p>
                    Live view of the job market represented by your indexed dataset.
                  </p>
                </div>

                <button className="btn btn-secondary" onClick={load}>
                  <Activity size={16} />
                  Refresh data
                </button>

              </div>


              {/* Statistics */}
              <div className="stat-grid">

                <Stat
                  icon={<BriefcaseBusiness />}
                  label="Jobs analyzed"
                  value={stats.total_jobs}
                  note="Indexed postings"
                />

                <Stat
                  icon={<Code2 />}
                  label="Skills identified"
                  value={stats.total_skills}
                  note="Unique skill terms"
                />

                <Stat
                  icon={<Globe2 />}
                  label="Countries"
                  value={stats.countries.length}
                  note="In current dataset"
                />

                <Stat
                  icon={<TrendingUp />}
                  label="Industries"
                  value={stats.industries.length}
                  note="Represented sectors"
                />

              </div>


              {/* Top skills and countries */}
              <div className="two-col">

                <div className="panel">

                  <PanelTitle
                    title="Most demanded skills"
                    subtitle="Frequency in indexed job postings"
                  />

                  <div className="chart-wrap">

                    <ResponsiveContainer width="100%" height={260}>

                      <BarChart
                        data={topSkills}
                        layout="vertical"
                        margin={{ left: 10, right: 18 }}
                      >

                        <CartesianGrid
                          strokeDasharray="3 3"
                          stroke="var(--line)"
                        />

                        <XAxis
                          type="number"
                          tick={{ fill: 'var(--muted)', fontSize: 11 }}
                          axisLine={false}
                        />

                        <YAxis
                          dataKey="skill"
                          type="category"
                          width={105}
                          tick={{ fill: 'var(--muted)', fontSize: 11 }}
                          axisLine={false}
                        />

                        <Tooltip
                          contentStyle={{
                            background: 'var(--panel)',
                            border: '1px solid var(--line)',
                            borderRadius: 12,
                            color: 'var(--text)'
                          }}
                        />

                        <Bar
                          dataKey="count"
                          fill="#8b7cff"
                          radius={[0, 6, 6, 0]}
                        />

                      </BarChart>

                    </ResponsiveContainer>

                  </div>
                </div>


                <div className="panel">

                  <PanelTitle
                    title="Market distribution"
                    subtitle="Job postings by country"
                  />

                  {stats.countries.map((c, i) => (
                    <div className="distribution" key={c.name}>

                      <div>
                        <span>{c.name}</span>
                        <b>{c.count.toLocaleString()}</b>
                      </div>

                      <div className="progress">
                        <i
                          style={{
                            width: `${Math.max(
                              4,
                              c.count /
                              Math.max(1, stats.countries[0]?.count) * 100
                            )}%`
                          }}
                        />
                      </div>

                    </div>
                  ))}

                  {!stats.countries.length && <Empty />}

                </div>

              </div>


              {/* Industry and experience charts */}
              <div className="two-col">

                <div className="panel">

                  <PanelTitle
                    title="Industry distribution"
                    subtitle="Job postings across industries"
                  />

                  <div className="chart-wrap">

                    <ResponsiveContainer width="100%" height={260}>

                      <BarChart
                        data={stats.industries}
                        layout="vertical"
                        margin={{ left: 10, right: 18 }}
                      >

                        <CartesianGrid
                          strokeDasharray="3 3"
                          stroke="var(--line)"
                        />

                        <XAxis
                          type="number"
                          tick={{
                            fill: 'var(--muted)',
                            fontSize: 11
                          }}
                        />

                        <YAxis
                          dataKey="name"
                          type="category"
                          width={110}
                          tick={{
                            fill: 'var(--muted)',
                            fontSize: 10
                          }}
                        />

                        <Tooltip
                          contentStyle={{
                            background: 'var(--panel)',
                            border: '1px solid var(--line)',
                            borderRadius: 12,
                            color: 'var(--text)'
                          }}
                        />

                        <Bar
                          dataKey="count"
                          fill="#54cdb8"
                          radius={[0, 6, 6, 0]}
                        />

                      </BarChart>

                    </ResponsiveContainer>

                  </div>

                </div>


                <div className="panel">

                  <PanelTitle
                    title="Experience distribution"
                    subtitle="Jobs by experience level"
                  />

                  <div className="chart-wrap">

                    <ResponsiveContainer width="100%" height={260}>

                      <BarChart
                        data={experienceData}
                        margin={{
                          top: 10,
                          right: 15,
                          bottom: 10,
                          left: 0
                        }}
                      >

                        <CartesianGrid
                          strokeDasharray="3 3"
                          stroke="var(--line)"
                        />

                        <XAxis
                          dataKey="experience"
                          tick={{
                            fill: 'var(--muted)',
                            fontSize: 10
                          }}
                        />

                        <YAxis
                          tick={{
                            fill: 'var(--muted)',
                            fontSize: 11
                          }}
                        />

                        <Tooltip
                          contentStyle={{
                            background: 'var(--panel)',
                            border: '1px solid var(--line)',
                            borderRadius: 12,
                            color: 'var(--text)'
                          }}
                        />

                        <Bar
                          dataKey="count"
                          fill="#8b7cff"
                          radius={[6, 6, 0, 0]}
                        />

                      </BarChart>

                    </ResponsiveContainer>

                  </div>

                </div>

              </div>


              {/* Recent jobs */}
              <div className="panel">

                <PanelTitle
                  title="Recent opportunities"
                  subtitle="Latest postings in the indexed dataset"
                  action={
                    <button
                      className="text-btn"
                      onClick={() => go('Jobs')}
                    >
                      View all <ArrowUpRight size={14} />
                    </button>
                  }
                />

                <JobTable jobs={jobs.slice(0, 5)} />

              </div>


              {!user && (
                <AuthCard
                  auth={auth}
                  setAuth={setAuth}
                  authMode={authMode}
                  setAuthMode={setAuthMode}
                  submitAuth={submitAuth}
                  loading={loading}
                />
              )}

            </>
          )}


          {/* JOBS */}
          {page === 'Jobs' && (
            <>

              <PageHead
                title="Explore jobs"
                desc="Search postings across roles, locations and industries."
              />

              <form className="searchbar" onSubmit={searchJobs}>
                <Search />

                <input
                  value={query}
                  onChange={e => setQuery(e.target.value)}
                  placeholder="Search job title, company, skill or keyword..."
                />

                <button className="btn btn-primary">
                  Search jobs
                </button>
              </form>

              <div className="panel">
                <JobTable jobs={jobs} />
              </div>

            </>
          )}


          {/* SKILL INSIGHTS */}
          {page === 'Skill Insights' && (
            <>

              <PageHead
                title="Skill intelligence"
                desc="Explore skill demand and the jobs where skills appear."
              />

              <div className="searchbar">
                <Search />

                <input
                  value={skill}
                  onChange={e => setSkill(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && inspectSkill()}
                  placeholder="Enter a skill, e.g. Python"
                />

                <button
                  className="btn btn-primary"
                  onClick={inspectSkill}
                >
                  Analyze skill
                </button>
              </div>


              {detail && (
                <div className="panel insight-panel">

                  {detail.error ? (
                    <p>{detail.error}</p>
                  ) : (
                    <>

                      <div className="insight-top">

                        <div>
                          <span className="eyebrow">SKILL REPORT</span>
                          <h2>{detail.skill}</h2>
                        </div>

                        <div className="big-number">
                          {detail.job_count.toLocaleString()}
                          <small>matching jobs</small>
                        </div>

                      </div>


                      <div className="stat-grid compact">

                        <Stat
                          label="Countries"
                          value={Object.keys(detail.countries || {}).length}
                        />

                        <Stat
                          label="Industries"
                          value={Object.keys(detail.industries || {}).length}
                        />

                        <Stat
                          label="Average salary floor"
                          value={
                            detail.average_salary_min
                              ? `${detail.currency} ${detail.average_salary_min.toLocaleString()}`
                              : 'N/A'
                          }
                        />

                      </div>


                      <div className="tag-row">
                        {detail.related_skills?.map(x => (
                          <span className="skill-tag" key={x.skill}>
                            {x.skill} · {x.count}
                          </span>
                        ))}
                      </div>

                      <p className="subtle-note">{detail.note}</p>

                    </>
                  )}

                </div>
              )}

            </>
          )}


          {/* COMPARE SKILLS */}
          {page === 'Compare Skills' && (
            <>

              <PageHead
                title="Compare skills"
                desc="Compare demand signals across skills using the same indexed dataset."
              />

              <div className="panel">

                <label>Skills (comma separated, 2–5)</label>

                <div className="searchbar">

                  <input
                    value={compare}
                    onChange={e => setCompare(e.target.value)}
                  />

                  <button
                    className="btn btn-primary"
                    onClick={compareSkills}
                  >
                    Compare
                  </button>

                </div>


                {comp && (
                  <div className="compare-grid">

                    {comp.comparison.map((x, i) => (
                      <div className="compare-card" key={x.skill}>

                        <span className="eyebrow">
                          SKILL 0{i + 1}
                        </span>

                        <h2>{x.skill}</h2>

                        <strong>{x.job_count.toLocaleString()}</strong>

                        <small>matching postings</small>

                        <div className="compare-meta">
                          <span>{x.countries} countries</span>
                          <span>{x.industries} industries</span>
                        </div>

                      </div>
                    ))}

                  </div>
                )}

              </div>

            </>
          )}


          {/* PROFILE */}
          {page === 'My Profile' && (
            <>

              <PageHead
                title="Your career profile"
                desc="Add your skills and target role to power personalized recommendations."
              />

              <div className="panel form-panel">

                <form onSubmit={saveProfile}>

                  <label>Target job role</label>

                  <input
                    value={profile.target_role}
                    onChange={e =>
                      setProfile({
                        ...profile,
                        target_role: e.target.value
                      })
                    }
                    placeholder="e.g. Data Analyst"
                  />

                  <label>Your skills (comma separated)</label>

                  <textarea
                    rows="4"
                    value={profile.skills}
                    onChange={e =>
                      setProfile({
                        ...profile,
                        skills: e.target.value
                      })
                    }
                    placeholder="Python, SQL, Excel..."
                  />

                  <div className="form-actions">

                    <button className="btn btn-primary">
                      Save profile
                    </button>

                    <label className="btn btn-secondary upload-btn">
                      <Upload size={16} />
                      Analyze PDF resume

                      <input
                        type="file"
                        accept="application/pdf"
                        hidden
                        onChange={uploadResume}
                      />
                    </label>

                  </div>

                </form>

              </div>

            </>
          )}


          {/* RECOMMENDATIONS */}
          {page === 'Recommendations' && (
            <>

              <PageHead
                title="Skill development plan"
                desc="Recommendations based on your current skills, target role and indexed job data."
              />

              <div className="two-col">

                <div className="panel">

                  <PanelTitle
                    title="Recommended skills"
                    subtitle={recs?.target_role || 'Set a target role in your profile'}
                  />

                  {recs?.recommendations?.map(r => (
                    <div className="recommend-row" key={r.skill}>

                      <div>
                        <b>{r.skill}</b>
                        <small>{r.reason}</small>
                      </div>

                      <span className="count-pill">
                        {r.job_count} jobs
                      </span>

                    </div>
                  )) || <Empty />}

                </div>


                <div className="panel">

                  <PanelTitle
                    title="Your skill gap"
                    subtitle="Frequently requested skills for your target role"
                  />

                  <div className="tag-row">

                    {gap?.matched?.map(s => (
                      <span className="skill-tag good" key={s}>
                        ✓ {s}
                      </span>
                    ))}

                  </div>

                  <h4>Skills to develop</h4>

                  <div className="tag-row">

                    {gap?.missing?.map(s => (
                      <span className="skill-tag" key={s}>
                        {s}
                      </span>
                    ))}

                  </div>

                  {gap?.jobs_analyzed === 0 && (
                    <Empty text="No matching job data. Try a broader target role." />
                  )}

                </div>

              </div>

            </>
          )}


          {/* ADMIN */}
          {page === 'Admin' && (
            <>

              <PageHead
                title="Admin console"
                desc="Monitor indexed data and import authorized job datasets."
              />

              <div className="stat-grid">

                <Stat
                  icon={<Users />}
                  label="Registered users"
                  value={admin?.users ?? '—'}
                />

                <Stat
                  icon={<BriefcaseBusiness />}
                  label="Indexed jobs"
                  value={admin?.jobs ?? '—'}
                />

                <Stat
                  icon={<Database />}
                  label="Ingestion runs"
                  value={admin?.runs?.length ?? 0}
                />

              </div>


              <div className="panel">

                <PanelTitle
                  title="Import job dataset"
                  subtitle="Upload a CSV containing title, company, location and description."
                />

                <label className="btn btn-primary upload-btn">
                  <Upload size={16} />
                  Choose CSV file

                  <input
                    type="file"
                    accept=".csv"
                    hidden
                    onChange={uploadCsv}
                  />
                </label>

                <p className="subtle-note">
                  CSV import detects skills from descriptions if a skills
                  column is not supplied. Duplicate title/company/location
                  combinations are skipped.
                </p>

              </div>


              <div className="panel">

                <PanelTitle title="Recent ingestion runs" />

                {admin?.runs?.map(r => (
                  <div className="recommend-row" key={r.id}>

                    <div>
                      <b>{r.source}</b>
                      <small>
                        {r.created_at} · {r.message}
                      </small>
                    </div>

                    <span className="status-pill">
                      {r.status} · {r.records_added}
                    </span>

                  </div>
                )) || <Empty />}

              </div>

            </>
          )}


          <footer>
            SkillScope <span>•</span> Job Market Skill Trend Analyzer
            <span>•</span>
            Analytics reflect ingested data, not the entire labor market.
          </footer>

        </div>
      </main>

    </div>
  );
}



// Reusable components

function Stat({ icon, label, value, note }) {
  return (
    <div className="stat-card">

      <div className="stat-icon">
        {icon || <Activity size={17} />}
      </div>

      <span>{label}</span>

      <strong>
        {typeof value === 'number'
          ? value.toLocaleString()
          : value}
      </strong>

      <small>{note || 'Current dataset'}</small>

    </div>
  );
}


function PanelTitle({ title, subtitle, action }) {
  return (
    <div className="panel-title">

      <div>
        <h3>{title}</h3>
        {subtitle && <p>{subtitle}</p>}
      </div>

      {action}

    </div>
  );
}


function PageHead({ title, desc }) {
  return (
    <div className="page-heading">

      <div>
        <div className="eyebrow">WORKSPACE / ANALYTICS</div>
        <h1>{title}</h1>
        <p>{desc}</p>
      </div>

    </div>
  );
}


function JobTable({ jobs }) {
  return jobs?.length ? (

    <div className="table-wrap">

      <table>

        <thead>
          <tr>
            <th>ROLE</th>
            <th>COMPANY</th>
            <th>LOCATION</th>
            <th>INDUSTRY</th>
            <th>SKILLS</th>
          </tr>
        </thead>

        <tbody>

          {jobs.map(j => (
            <tr key={j.id}>

              <td>
                <b>{j.title}</b>
                <small>{j.experience_level}</small>
              </td>

              <td>{j.company}</td>

              <td>{j.location}, {j.country}</td>

              <td>{j.industry}</td>

              <td>
                <div className="tag-row">

                  {j.skills.slice(0, 3).map(s => (
                    <span className="mini-tag" key={s}>
                      {s}
                    </span>
                  ))}

                </div>
              </td>

            </tr>
          ))}

        </tbody>

      </table>

    </div>

  ) : (
    <Empty text="No job postings available." />
  );
}


function Empty({ text = 'No data available yet.' }) {
  return (
    <div className="empty">
      <Database size={22} />
      <span>{text}</span>
    </div>
  );
}


function AuthCard({
  auth,
  setAuth,
  authMode,
  setAuthMode,
  submitAuth,
  loading
}) {
  return (

    <div className="auth-card" id="auth">

      <div>
        <span className="eyebrow">GET PERSONALIZED</span>

        <h2>Create your workspace</h2>

        <p>
          Sign in to save skills, analyze your resume
          and get a personalized skill gap report.
        </p>
      </div>


      <form onSubmit={submitAuth}>

        {authMode === 'register' && (
          <input
            required
            placeholder="Full name"
            value={auth.name}
            onChange={e =>
              setAuth({ ...auth, name: e.target.value })
            }
          />
        )}

        <input
          type="email"
          required
          placeholder="Email"
          value={auth.email}
          onChange={e =>
            setAuth({ ...auth, email: e.target.value })
          }
        />

        <input
          type="password"
          required
          minLength="8"
          placeholder="Password"
          value={auth.password}
          onChange={e =>
            setAuth({ ...auth, password: e.target.value })
          }
        />

        {authMode === 'register' && (
          <select
            value={auth.role}
            onChange={e =>
              setAuth({ ...auth, role: e.target.value })
            }
          >
            <option value="student">Student / Job seeker</option>
            <option value="recruiter">Recruiter</option>
          </select>
        )}

        <button className="btn btn-primary" disabled={loading}>
          {loading
            ? 'Please wait...'
            : authMode === 'login'
              ? 'Sign in'
              : 'Create account'}
        </button>

        <button
          type="button"
          className="text-btn"
          onClick={() =>
            setAuthMode(
              authMode === 'login' ? 'register' : 'login'
            )
          }
        >
          {authMode === 'login'
            ? 'Create an account'
            : 'Already have an account? Sign in'}
        </button>

      </form>

    </div>
  );
}


export default App;
