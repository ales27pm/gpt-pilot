import { useEffect, useState } from 'react';

export default function App() {
  const [projects, setProjects] = useState([]);
  const [name, setName] = useState('');
  const [message, setMessage] = useState('');
  const [msgType, setMsgType] = useState('info');

  async function load() {
    setMessage('Loading...');
    setMsgType('info');
    try {
      const res = await fetch('/api/projects');
      if (!res.ok) throw new Error('Failed to load projects');
      const data = await res.json();
      setProjects(data.projects);
      setMessage('');
    } catch (err) {
      setMessage(err.message || 'Failed to load projects');
      setMsgType('error');
    }
  }

  async function create(e) {
    e.preventDefault();
    try {
      const resp = await fetch('/api/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name }),
      });
      if (!resp.ok) throw new Error('Failed to create project');
      setMessage('Project created');
      setMsgType('success');
      setName('');
      await load();
    } catch (err) {
      setMessage(err.message || 'Failed to create project');
      setMsgType('error');
    }
  }

  async function remove(id, projName) {
    if (!confirm(`Delete project "${projName}"?`)) return;
    try {
      const resp = await fetch(`/api/projects/${id}`, { method: 'DELETE' });
      if (!resp.ok) throw new Error('Failed to delete project');
      setMessage('Project deleted');
      setMsgType('success');
      await load();
    } catch (err) {
      setMessage(err.message || 'Failed to delete project');
      setMsgType('error');
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <>
      <header className="top-bar">
        <h1>GPT Pilot Projects</h1>
        <button onClick={load}>Refresh</button>
      </header>
      <main className="container">
        <form onSubmit={create} className="create">
          <label htmlFor="new-name" className="visually-hidden">
            Project name
          </label>
          <input
            id="new-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="New project name"
            required
          />
          <button type="submit">Create</button>
        </form>
        {message && <p className={`message ${msgType}`}>{message}</p>}
        <ul className="project-list">
          {projects.length === 0 ? (
            <li className="empty">No projects yet</li>
          ) : (
            projects.map((project) => (
              <li key={project.id}>
                <div className="project-header">
                  <h2>{project.name}</h2>
                  <button onClick={() => remove(project.id, project.name)}>
                    Delete
                  </button>
                </div>
                <p>
                  ID: {project.id} | Updated: {project.updated_at ?? 'never'}
                </p>
                <ul>
                  {project.branches.map((branch) => (
                    <li key={branch.id}>
                      <div>
                        {branch.name} ({branch.id})
                      </div>
                      <ul>
                        {branch.steps.map((s) => (
                          <li key={s.step}>
                            {s.step}: {s.name}
                          </li>
                        ))}
                      </ul>
                    </li>
                  ))}
                </ul>
              </li>
            ))
          )}
        </ul>
      </main>
    </>
  );
}
